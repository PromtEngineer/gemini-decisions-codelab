"""Voice agent reflexes: decide what to do with a caller's audio, with no transcription step.

    python reflex.py                 # every clip in samples/
    python reflex.py my_clip.wav     # your own recording (.wav, .mp3 or .m4a)
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decide import choice, decide, media, score, yes_no

HERE = pathlib.Path(__file__).parent
CUTOFF = 0.80

QUESTIONS = {
    "turn_finished": yes_no("Has the caller finished speaking, so the assistant can reply now?",
                            yes="The last sentence is complete.", no="The caller stops mid-sentence or is still searching for words."),
    "wants_human": yes_no("Is the caller asking to speak to a human agent?"),
    "intent": choice("What does the caller want?", {
        "opening_hours": "Asks when the business is open.",
        "order_or_refund_status": "Asks about an order, delivery or refund.",
        "talk_to_a_person": "Wants a human agent, or is complaining about the bot.",
        "end_call": "Is saying goodbye.",
        "other": "Anything else.",
    }),
    "frustration": score("How frustrated does the caller sound?", ["Calm.", "Mildly annoyed.", "Clearly frustrated or angry."]),
}


def reflex(a):
    """Plain code turns the answers into what the voice agent does next."""
    if a["wants_human"].noul >= CUTOFF:
        return "HAND OFF to a person"
    if a["turn_finished"].noul < 0.5:
        return "KEEP LISTENING"
    if a["turn_finished"].confidence < CUTOFF:
        return "WAIT a moment, then check again"
    if a["intent"].choice == "end_call":
        return "SAY GOODBYE and hang up"
    return f"ANSWER ({a['intent'].choice})"


def main():
    clips = [pathlib.Path(p) for p in sys.argv[1:]] or sorted((HERE / "samples").glob("*.wav"))
    print(f"{'clip':24} {'finished':>8} {'human':>6} {'intent':24} {'frustr.':>7}  {'action':34} {'ms':>5}")
    for clip in clips:
        a, info = decide([media(clip)], QUESTIONS)
        print(f"{clip.stem:24} {a['turn_finished'].noul:8.2f} {a['wants_human'].noul:6.2f} {a['intent'].choice:24} {a['frustration'].score:7.2f}  {reflex(a):34} {info['ms']:>5}")


if __name__ == "__main__":
    main()
