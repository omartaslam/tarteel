"""Quick regression: Husary Al-Ikhlas must transcribe to the right ayah."""
import os
import sys
import transcribe_quran as tq

SAMPLES = [
    ("/tmp/tarteel-test/husary_112001.mp3", 1, "قل هو الله احد"),
    ("/tmp/tarteel-test/husary_quiet.wav", 1, "قل هو الله احد"),
    ("/tmp/tarteel-test/husary_112002.mp3", 2, "الله الصمد"),
    ("/tmp/tarteel-test/husary_112003.mp3", 3, "لم يلد ولم يولد"),
    ("/tmp/tarteel-test/husary_112004.mp3", 4, "ولم يكن له كفوا احد"),
]

def main():
    present = [(p, v, b) for p, v, b in SAMPLES if os.path.exists(p)]
    if not present:
        print("SKIP: no husary samples under /tmp/tarteel-test/")
        return 0
    tq._load()
    failed = 0
    for path, verse, bare in present:
        info = tq.transcribe_path(path, verse=verse)
        ok = (
            info["heard_verse"] == verse
            and info["heard_match"] in ("exact", "close")
            and tq.normalize_ar(info["heard_arabic"]).replace(" ", "")
               == tq.normalize_ar(bare).replace(" ", "")
        )
        status = "OK" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"{status} v{verse}: arabic={info['heard_arabic']!r} ph={info['heard_phonetic']!r} "
              f"raw={info['heard_raw']!r} match={info['heard_match']}")
    return failed

if __name__ == "__main__":
    sys.exit(main())
