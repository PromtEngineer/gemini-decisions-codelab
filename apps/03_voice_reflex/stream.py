"""Replay a clip as if it were arriving live, and ask after every second of audio.

It shows the moment the agent would hand the call to a person, which can be
before the caller stops talking. Deciding when a caller has finished a turn
needs silence detection as well, so this replay only watches for the hand-off.

    python stream.py                          # samples/02_wants_a_person.wav
    python stream.py samples/05_refund_then_person.wav
"""
import io
import pathlib
import sys
import wave

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decide import decide, media, score, yes_no

HERE = pathlib.Path(__file__).parent
STEP_SECONDS = 1.0
CUTOFF = 0.80

QUESTIONS = {
    "wants_human": yes_no("Has the caller asked to speak to a human agent?"),
    "frustration": score("How frustrated does the caller sound so far?", ["Calm.", "Mildly annoyed.", "Clearly frustrated or angry."]),
}


def prefix(src, seconds):
    """The first `seconds` of a WAV file, as WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setparams(src.getparams())
        src.rewind()
        out.writeframes(src.readframes(int(seconds * src.getframerate())))
    return buf.getvalue()


def main():
    clip = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "samples" / "02_wants_a_person.wav"
    with wave.open(str(clip)) as src:
        length = src.getnframes() / src.getframerate()
        print(f"{clip.name}, {length:.1f} s\n{'heard':>6} {'human':>6} {'frustr.':>7} {'ms':>5}")
        t = STEP_SECONDS
        while True:
            t = min(t, length)
            a, info = decide([media(clip, data=prefix(src, t))], QUESTIONS)
            human = a["wants_human"].noul
            flag = "  <- sounds frustrated" if a["frustration"].score >= 1.5 and human < CUTOFF else ""
            print(f"{t:5.1f}s {human:6.2f} {a['frustration'].score:7.2f} {info['ms']:>5}{flag}")
            if human >= CUTOFF:
                print(f"\n-> HAND OFF to a person after {t:.1f} s of a {length:.1f} s clip")
                break
            if t >= length:
                print("\n-> No hand-off needed")
                break
            t += STEP_SECONDS


if __name__ == "__main__":
    main()
