"""A browser agent that reads each screen with one Decisions API call.

At every step it takes a screenshot and asks a fixed set of small yes/no
checks, plus which screen it is on. Plain code then picks the action. The page
is a local checkout form with a cookie banner, a bad email and an empty card field.

    python agent.py          # headless
    python agent.py --show   # watch the browser
"""
import pathlib
import sys
import time

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decide import choice, decide, media, yes_no

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
CUTOFF = 0.80  # if a check the agent needs is less sure than this, it stops for a person

# Small, single-purpose checks. The model answers them; code combines them.
QUESTIONS = {
    "screen": choice("Which screen is this?", {
        "checkout_form": "A form asking for email and payment details.",
        "processing": "A spinner or a message that the payment is being processed.",
        "order_confirmation": "A message that the order is confirmed.",
        "other": "Any other page.",
    }),
    "cookie_banner": yes_no("Is a cookie consent banner visible?"),
    "email_error": yes_no("Is an error message about the email address visible?"),
    # Without the two descriptions, the grey placeholder digits read as a filled field.
    "card_empty": yes_no("Is the card number field empty?",
                         yes="The field shows nothing or only light grey placeholder text.",
                         no="The field contains dark typed digits."),
    "button_enabled": yes_no("Is the 'Place order' button enabled and clickable?"),
}

# (check, expected answer, action name, what the code does), in priority order
RULES = [
    ("cookie_banner", True, "dismiss the cookie banner", lambda page: page.click("#reject")),
    ("email_error", True, "fix the email", lambda page: page.fill("#email", "sam@example.com")),
    ("card_empty", True, "enter the card number", lambda page: page.fill("#card", "4242 4242 4242 4242")),
    ("button_enabled", True, "click Place order", lambda page: page.click("#order")),
]


def pick_action(a):
    """Returns (action name, function) or (reason to stop, None)."""
    screen = a["screen"]
    if screen.confidence < CUTOFF:
        return f"stop: not sure which screen this is ({screen.choice}, {screen.confidence:.2f})", None
    if screen.choice == "order_confirmation":
        return "done", None
    if screen.choice == "processing":
        return "wait", lambda page: time.sleep(1.0)
    if screen.choice != "checkout_form":
        return "stop: unexpected screen", None
    for key, expected, name, act in RULES:
        if a[key].confidence < CUTOFF:
            return f"stop: not sure about {key} ({a[key].noul:.2f})", None
        if (a[key].noul >= 0.5) == expected:
            return name, act
    return "stop: nothing to do", None


def run(page, on_step=None, max_steps=12):
    """Runs the agent on an open page. Calls on_step(step, answers, action, info) after every decision."""
    page.goto((HERE / "shop" / "index.html").as_uri())
    name = "gave up"
    for step in range(1, max_steps + 1):
        shot = OUT / f"step_{step:02d}.png"
        page.screenshot(path=str(shot))
        a, info = decide([media(shot, resolution="high")], QUESTIONS)
        name, act = pick_action(a)
        if on_step:
            on_step(step, a, name, info)
        if act is None:
            break
        act(page)
        page.wait_for_timeout(200)
    return name, step


def main():
    OUT.mkdir(exist_ok=True)
    totals = {"ms": 0, "usd": 0.0, "actions": 0}

    def print_step(step, a, name, info):
        prob = lambda k: f"{a[k].noul:.2f}"
        totals["ms"] += info["ms"]
        totals["usd"] += info["usd"]
        totals["actions"] += not name.startswith(("stop", "done", "wait"))
        print(f"{step:<4} {a['screen'].choice:19} {prob('cookie_banner'):>6} {prob('email_error'):>6} {prob('card_empty'):>6} {prob('button_enabled'):>6}  {name:26} {info['ms']:>5}")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless="--show" not in sys.argv)
        page = browser.new_page(viewport={"width": 1100, "height": 720})
        print(f"{'step':4} {'screen':19} {'banner':>6} {'email':>6} {'card':>6} {'button':>6}  {'action':26} {'ms':>5}")
        name, steps = run(page, print_step)
        print(f"\nFinished with '{name}' after {totals['actions']} actions. {steps} decision calls took {totals['ms'] / 1000:.1f} s in total and cost ${totals['usd']:.5f} at the paid rate.")
        browser.close()


if __name__ == "__main__":
    main()
