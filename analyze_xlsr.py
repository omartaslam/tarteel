"""
XLSR-based analysis: forced-align with the diverse-speaker model (works on
ordinary voices), locate the qalqalah letter, run the trained classifier.
Replaces the MFA path in analyze.py.
"""
import torch, librosa, subprocess, os, pickle, numpy as np
import torchaudio.functional as TAF
from transformers import Wav2Vec2ForCTC, AutoProcessor
import transcribe_quran as tq

MID = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic"
CLF = os.path.join(os.path.dirname(__file__), "models", "qalqalah_clf_xlsr.pkl")

# verse text (no spaces->| handled below). Final letter is the qalqalah dal.
VTEXT = {1:"قل هو الله احد", 2:"الله الصمد", 3:"لم يلد ولم يولد", 4:"ولم يكن له كفوا احد"}

_proc=_model=_clf=None
def _load():
    global _proc,_model,_clf
    if _model is None:
        # Prefer local image cache; fall back to download if offline flags unset
        kw={"local_files_only": bool(os.environ.get("TRANSFORMERS_OFFLINE") or os.environ.get("HF_HUB_OFFLINE"))}
        try:
            _proc=AutoProcessor.from_pretrained(MID, **kw)
            _model=Wav2Vec2ForCTC.from_pretrained(MID, **kw); _model.eval()
        except Exception:
            _proc=AutoProcessor.from_pretrained(MID)
            _model=Wav2Vec2ForCTC.from_pretrained(MID); _model.eval()
        _clf=pickle.load(open(CLF,"rb"))
    # Quran Whisper for accurate "what I heard" (XLSR free-CTC is unreliable on tilawah)
    tq._load()
    return _proc,_model,_clf

HI=0.70
# Surface likely-error coaching a bit earlier than "confident correct",
# so learners get a retry tip instead of a blank "ask your teacher".
HI_ERROR=0.55


def _feat(y,sr,a,b):
    s=y[int(max(0,a-0.08)*sr):int((b+0.02)*sr)]
    if len(s)<128: return None
    mf=librosa.feature.mfcc(y=s,sr=sr,n_mfcc=13,n_fft=min(512,len(s)),hop_length=128)
    rms=librosa.feature.rms(y=s,hop_length=128)[0]
    return np.concatenate([mf.mean(1),mf.std(1),[rms.min(),rms.max(),rms.max()-rms.min(),len(s)/sr]])

class AnalysisCancelled(Exception):
    """Raised when the user starts a new recording and cancels this job."""


ONSET_WINDOW_S = 0.50


def onset_probe(emissions, proc, dur: float) -> dict:
    """Unconstrained read of the take's onset, for the ق vs ك decision.

    `emissions` are free log-softmax outputs — NOT forced-aligned. Forced
    alignment is constrained to the expected ayah, so it can only ever emit ق
    and would report ق for silence; that bug let the Qul stage pass anything.

    Returns {p_qaf, p_kaf, onset} where the probabilities are the strongest
    frame-level evidence for each letter inside the first ONSET_WINDOW_S of
    voiced audio.
    """
    vocab = proc.tokenizer.get_vocab()
    qaf, kaf = vocab.get("ق"), vocab.get("ك")
    blank = proc.tokenizer.pad_token_id
    if qaf is None or kaf is None:
        return {"p_qaf": 0.0, "p_kaf": 0.0, "onset": ""}
    probs = emissions.exp()[0]
    T = probs.shape[0]
    if not T or dur <= 0:
        return {"p_qaf": 0.0, "p_kaf": 0.0, "onset": ""}
    best = torch.argmax(probs, dim=-1)
    voiced = (best != blank).nonzero().flatten()
    start = int(voiced[0]) if len(voiced) else 0
    end = min(T, start + max(1, int(ONSET_WINDOW_S / dur * T)))
    win = probs[start:end]
    inv = {v: k for k, v in vocab.items()}
    letters, prev = [], None
    for tok in torch.argmax(win, dim=-1).tolist():
        if tok != prev and tok != blank:
            letters.append(inv.get(tok, ""))
        prev = tok
    return {
        "p_qaf": round(float(win[:, qaf].max()), 3),
        "p_kaf": round(float(win[:, kaf].max()), 3),
        "onset": "".join(letters)[:8],
    }


def analyze_verse(path, verse, on_progress=None, mastered=None, last_focus=None, cancel_check=None, stage_id=None, locked_stages=None, qu_bridge_attempt=None):
    def prog(pct, phase, msg):
        if cancel_check and cancel_check():
            raise AnalysisCancelled()
        if on_progress:
            try: on_progress(pct, phase, msg)
            except Exception: pass

    prog(3, "start", "Starting analysis…")
    proc,model,clf=_load()
    uid = f"{os.getpid()}_{id(path)}_{os.path.basename(path)}"
    orig = f"/tmp/xl_orig_{uid}.wav"
    wavp = f"/tmp/xl_{uid}.wav"
    try:
        prog(8, "decode", "Reading your recording…")
        # measure raw level first; if very quiet, apply hard gain before loudnorm
        subprocess.run(["ffmpeg","-i",path,"-ar","16000","-ac","1",orig,"-y"],capture_output=True)
        _pk=0.0
        try:
            if os.path.exists(orig):
                _probe,_=librosa.load(orig,sr=16000)
                _pk=float(np.abs(_probe).max()) if len(_probe) else 0.0
        except Exception:
            _pk=0.0
        gain = "volume=32dB," if _pk < 0.03 else ("volume=22dB," if _pk < 0.08 else ("volume=14dB," if _pk<0.15 else ""))
        prog(18, "normalize", "Cleaning & boosting the audio…")
        # dynamic compression evens out the quiet iOS capture, then normalize
        afilter = gain + "acompressor=threshold=-24dB:ratio=4:makeup=6," + "loudnorm=I=-14:TP=-1.5:LRA=11"
        subprocess.run(["ffmpeg","-i",path,
                        "-af",afilter,
                        "-ar","16000","-ac","1",wavp,"-y"],capture_output=True)
        if not os.path.exists(wavp):
            subprocess.run(["ffmpeg","-i",path,"-ar","16000","-ac","1",wavp,"-y"],capture_output=True)
        if not os.path.exists(wavp):
            return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":"audio_decode_failed",
                     "level":"defer","plain":"Could not read the recording. Try again.","scholarly":None}]
        wav,_=librosa.load(wavp,sr=16000)
        prog(30, "align_model", "Matching rhythm to the ayah…")
        iv=proc(wav,sampling_rate=16000,return_tensors="pt").input_values
        with torch.no_grad():
            logits=model(iv).logits
            emissions=torch.log_softmax(logits,dim=-1)
        prog(45, "transcribe", "Transcribing what you said (English + Arabic)…")
        # Accurate Quran ASR for the transparency panel
        try:
            heard_info=tq.transcribe_path(wavp, verse=verse)
        except Exception as e:
            heard_info={"heard_arabic":"","heard_phonetic":"","heard_raw":"",
                        "heard_match":f"error:{e}","heard_verse":None,
                        "matched_arabic":"","matched_phonetic":""}
        if cancel_check and cancel_check():
            raise AnalysisCancelled()
        # Stage-scoped compare: only current stage words (not whole ayah yellow)
        try:
            import coaching as _coach_early
            import stages as _stg_early
            _st = _stg_early.get_stage(verse, stage_id) if stage_id else None
            _sw = list((_st or {}).get("words") or []) if _st else None
            if _st and _st.get("drill"):
                heard_info["compare_html"] = ""  # drill path sets its own compare
            else:
                heard_info["compare_html"] = _coach_early.compare_html(
                    verse,
                    heard_info.get("heard_arabic") or heard_info.get("heard_raw") or "",
                    heard_info.get("heard_phonetic") or "",
                    stage_words=_sw if _sw is not None else None,
                )
        except Exception:
            heard_info["compare_html"] = ""
        # Read ق vs ك from the free emissions BEFORE forced alignment, which
        # would only ever hand back the expected ayah's letters.
        try:
            probe=onset_probe(emissions, proc, len(wav)/16000)
        except Exception:
            probe={"p_qaf":0.0,"p_kaf":0.0,"onset":""}
        prog(70, "align", "Lining up letters to the expected ayah…")
        vocab=proc.tokenizer.get_vocab()
        text=VTEXT[verse]
        ids=[vocab[c] for c in text.replace(" ","|") if c in vocab]
        targets=torch.tensor([ids],dtype=torch.int32)
        try:
            aligned,_=TAF.forced_align(emissions,targets,blank=proc.tokenizer.pad_token_id)
        except Exception as e:
            return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":f"align_error:{e}",
                     "level":"defer","plain":"Could not align the recording to the ayah. Try again.",
                     **heard_info}]
        frames=aligned[0].tolist(); T=len(frames); dur=len(wav)/16000
        inv={v:k for k,v in vocab.items()}
        pad=proc.tokenizer.pad_token_id
        dal_id=vocab.get("د")
        dal_frames=[i for i,t in enumerate(frames) if t==dal_id]
        import stages as stg
        needs_q = stg.stage_needs_qalqalah(verse, stage_id)

        peak=0.0; rmslev=0.0
        try:
            wproc,_=librosa.load(wavp,sr=16000)
            if len(wproc):
                peak=float(np.abs(wproc).max()); rmslev=float(np.sqrt((wproc**2).mean()))
        except Exception:
            pass
        raw_peak=_pk
        quality = "good" if (rmslev>0.03) else ("too_quiet" if raw_peak<0.008 else "ok")
        letters=[]
        prev=None
        for i,tok in enumerate(frames):
            if tok!=prev and tok!=pad:
                letters.append({"c":inv.get(tok,str(tok)),"t":round(i/T*dur,3)})
            prev=tok
        heard_ar = heard_info.get("heard_arabic","") or heard_info.get("heard_raw","")
        heard_ph = heard_info.get("heard_phonetic","")
        diag={"audio_quality":quality,"peak":round(peak,3),"rms_level":round(rmslev,4),
              "duration":round(dur,2),"letters":letters,"onset_probe":probe,
              "heard_arabic":heard_info.get("heard_arabic",""),
              "heard_phonetic":heard_ph,
              "heard_raw":heard_info.get("heard_raw",""),
              "heard_match":heard_info.get("heard_match",""),
              "heard_verse":heard_info.get("heard_verse"),
              "matched_arabic":heard_info.get("matched_arabic",""),
              "matched_phonetic":heard_info.get("matched_phonetic",""),
              "compare_html": heard_info.get("compare_html","")}

        qcard=None
        if not dal_frames:
            if needs_q:
                return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":"no_dal_found",
                         "level":"defer","plain":"Could not find the final dal in the recording.",
                         **diag}]
            # Word/drill stage — no bounce letter required; coach from ASR only.
            prog(92, "coach", "Writing your next-step tips…")
        else:
            a=dal_frames[0]/T*dur; b=(dal_frames[-1]+1)/T*dur
            b=max(b, a+0.12)
            prog(82, "tajweed", "Checking length, doubling & final bounce…")
            y22,_=librosa.load(wavp,sr=22050)
            f=_feat(y22,22050,a,b)
            if f is None:
                if needs_q:
                    return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":"feat_none",**diag}]
                prog(92, "coach", "Writing your next-step tips…")
            elif needs_q:
                proba=clf.predict_proba([f])[0][1]; conf=abs(proba-0.5)*2
                if proba>0.5:
                    verdict="error" if conf>=HI_ERROR else "defer"
                else:
                    verdict="correct" if conf>=HI else "defer"
                prog(92, "coach", "Writing your next-step tips…")
                import explanations as ex
                qfb=ex.qalqalah_feedback(verse, verdict, round(float(conf),2), p_error=round(float(proba),2))
                qcard={**qfb,"rule":"qalqalah","verse":verse,
                       "confidence":round(float(conf),2),"p_error":round(float(proba),2),
                       "dal_start":round(a,3),"dal_end":round(b,3)}
            else:
                # Dal frames exist from full-ayah forced align, but this stage
                # does not include the bounce word — skip the classifier.
                prog(92, "coach", "Writing your next-step tips…")

        import elements as el
        cards=el.build_feedback(
            verse, diag["letters"], qcard,
            heard_arabic=heard_ar,
            heard_phonetic=heard_ph,
            mastered=mastered,
            last_focus=last_focus,
            stage_id=stage_id,
            locked_stages=locked_stages,
            qu_bridge_attempt=qu_bridge_attempt,
            onset_probe=probe,
        )
        # Keep literal Whisper in heard_raw; drill stages override the shown heard_*.
        if cards:
            shown = cards[0]
            if shown.get("heard_match") == "drill":
                diag = {
                    **diag,
                    "heard_arabic": shown.get("heard_arabic", diag.get("heard_arabic", "")),
                    "heard_phonetic": shown.get("heard_phonetic", diag.get("heard_phonetic", "")),
                    "compare_html": shown.get("compare_html", ""),
                    "heard_match": "drill",
                    "matched_arabic": "",
                    "matched_phonetic": "",
                }
            cards[0] = {**shown, **diag}
        prog(100, "done", "Done")
        return cards
    finally:
        for p in (orig, wavp):
            try:
                if os.path.exists(p): os.unlink(p)
            except Exception:
                pass

if __name__=="__main__":
    import sys
    p=sys.argv[1] if len(sys.argv)>1 else "/home/anon/Downloads/New_Recording_22.m4a"
    v=int(sys.argv[2]) if len(sys.argv)>2 else 1
    for x in analyze_verse(p,v): print(x)
