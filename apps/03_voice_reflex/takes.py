"""Take checker: listen to clips from a narration recording and flag the ones where the speaker restarts.

A check for "does the clip end mid-sentence" was not reliable on real narration, so it is not used here.

    python takes.py my_voice/        # a folder of .wav, .mp3 or .m4a clips
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decide import choice, decide, media, score, yes_no

QUESTIONS = {
    "restart": yes_no("Does the speaker stumble and restart a phrase?",
                      yes="A phrase is started, abandoned and said again.", no="Every phrase is said once, without a restart."),
    "topic": choice("What is the speaker talking about?", {
        "benchmark_ranking": "How a model ranks or scores against others.",
        "what_agents_built": "Something that AI agents built or did.",
        "price_and_availability": "Price, plans or who can use it.",
        "other": "Anything else.",
    }),
    "energy": score("How energetic is the delivery?", ["Flat.", "Steady.", "Lively."]),
}


def verdict(a):
    p = a["restart"].noul
    if p >= 0.5:
        return "RETAKE: restart in the clip"
    if p >= 0.35:
        return "LISTEN: not sure"
    return "KEEP"


def main():
    folder = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent / "my_voice"
    clips = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".wav", ".mp3", ".m4a"))
    print(f"{'clip':24} {'restart':>7} {'topic':24} {'energy':>6}  {'verdict':28} {'ms':>5}")
    for clip in clips:
        a, info = decide([media(clip)], QUESTIONS)
        print(f"{clip.stem:24} {a['restart'].noul:7.2f} {a['topic'].choice:24} {a['energy'].score:6.2f}  {verdict(a):28} {info['ms']:>5}")


if __name__ == "__main__":
    main()
