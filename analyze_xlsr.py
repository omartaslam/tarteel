"""
XLSR-based analysis: forced-align with the diverse-speaker model (works on
ordinary voices), locate the qalqalah letter, run the trained classifier.
Replaces the MFA path in analyze.py.
"""
import torch, librosa, subprocess, os, pickle, numpy as np
import torchaudio.functional as TAF
from transformers import Wav2Vec2ForCTC, AutoProcessor

MID = "jonatasgrosman/wav2vec2-large-xlsr-53-arabic"
CLF = os.path.join(os.path.dirname(__file__), "models", "qalqalah_clf_xlsr.pkl")

# verse text (no spaces->| handled below). Final letter is the qalqalah dal.
VTEXT = {1:"قل هو الله احد", 2:"الله الصمد", 3:"لم يلد ولم يولد", 4:"ولم يكن له كفوا احد"}

_proc=_model=_clf=None
def _load():
    global _proc,_model,_clf
    if _model is None:
        _proc=AutoProcessor.from_pretrained(MID)
        _model=Wav2Vec2ForCTC.from_pretrained(MID); _model.eval()
        _clf=pickle.load(open(CLF,"rb"))
    return _proc,_model,_clf

HI=0.70

def _feat(y,sr,a,b):
    s=y[int(max(0,a-0.08)*sr):int((b+0.02)*sr)]
    if len(s)<128: return None
    mf=librosa.feature.mfcc(y=s,sr=sr,n_mfcc=13,n_fft=min(512,len(s)),hop_length=128)
    rms=librosa.feature.rms(y=s,hop_length=128)[0]
    return np.concatenate([mf.mean(1),mf.std(1),[rms.min(),rms.max(),rms.max()-rms.min(),len(s)/sr]])

def analyze_verse(path, verse):
    proc,model,clf=_load()
    subprocess.run(["ffmpeg","-i",path,"-ar","16000","-ac","1","/tmp/xl.wav","-y"],capture_output=True)
    wav,_=librosa.load("/tmp/xl.wav",sr=16000)
    iv=proc(wav,sampling_rate=16000,return_tensors="pt").input_values
    with torch.no_grad():
        emissions=torch.log_softmax(model(iv).logits,dim=-1)
    vocab=proc.tokenizer.get_vocab()
    text=VTEXT[verse]
    ids=[vocab[c] for c in text.replace(" ","|") if c in vocab]
    targets=torch.tensor([ids],dtype=torch.int32)
    try:
        aligned,_=TAF.forced_align(emissions,targets,blank=proc.tokenizer.pad_token_id)
    except Exception as e:
        return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":f"align_error:{e}"}]
    frames=aligned[0].tolist(); T=len(frames); dur=len(wav)/16000
    inv={v:k for k,v in vocab.items()}
    pad=proc.tokenizer.pad_token_id
    # find the LAST 'د' (dal) - the qalqalah position
    dal_id=vocab.get("د")
    dal_frames=[i for i,t in enumerate(frames) if t==dal_id]
    if not dal_frames:
        return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":"no_dal_found"}]
    a=dal_frames[0]/T*dur; b=(dal_frames[-1]+1)/T*dur
    # XLSR marks letter ONSET, not full duration - widen to capture the
    # qalqalah release burst that follows (classifier trained on ~100ms windows)
    b=max(b, a+0.12)
    y22,_=librosa.load("/tmp/xl.wav",sr=22050)
    f=_feat(y22,22050,a,b)
    # --- diagnostics: audio quality + full letter alignment ---
    peak=float(np.abs(wav).max()); level=float(np.sqrt((wav**2).mean()))
    quality = "good" if (peak>0.1 and peak<0.99 and level>0.02) else \
              ("too_quiet" if level<=0.02 else "clipping" if peak>=0.99 else "ok")
    letters=[]
    prev=None
    for i,tok in enumerate(frames):
        if tok!=prev and tok!=pad:
            letters.append({"c":inv.get(tok,str(tok)),"t":round(i/T*dur,3)})
        prev=tok
    diag={"audio_quality":quality,"peak":round(peak,3),"level":round(level,4),
          "duration":round(dur,2),"letters":letters}
    if f is None:
        return [{"rule":"qalqalah","verdict":"defer","confidence":0.0,"reason":"feat_none",**diag}]
    proba=clf.predict_proba([f])[0][1]; conf=abs(proba-0.5)*2
    verdict="defer" if conf<HI else ("error" if proba>0.5 else "correct")
    return [{"rule":"qalqalah","verse":verse,"verdict":verdict,
             "confidence":round(float(conf),2),"p_error":round(float(proba),2),
             "dal_start":round(a,3),"dal_end":round(b,3),**diag}]

if __name__=="__main__":
    import sys
    p=sys.argv[1] if len(sys.argv)>1 else "/home/anon/Downloads/New_Recording_22.m4a"
    v=int(sys.argv[2]) if len(sys.argv)>2 else 1
    for x in analyze_verse(p,v): print(x)
