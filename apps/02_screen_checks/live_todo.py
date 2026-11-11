"""The same idea on a live site: Playwright's public TodoMVC demo.

The agent has a goal (three to-dos, the first one completed). After every
action it takes a screenshot and asks the Decisions API what is on the page.
Code compares the answers with the goal and picks the next action.

    python live_todo.py          # headless
    python live_todo.py --show   # watch the browser
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decide import choice, decide, media, yes_no

HERE = pathlib.Path(__file__).parent
OUT = HERE / "out"
URL = "https://demo.playwright.dev/todomvc/"
CUTOFF = 0.80
TODOS = ["Record the video", "Publish the codelab", "Reply to comments"]
DONE = TODOS[0]  # this one should end up completed

QUESTIONS = {
    **{f"has_{i}": yes_no(f"Does the to-do list contain an item with the text '{t}'?") for i, t in enumerate(TODOS)},
    "first_done": yes_no(f"Is the item '{DONE}' marked as completed?",
                         yes="Its circle is ticked and its text is greyed out or struck through.",
                         no="Its circle is empty, or the item is not in the list."),
    "items_left": choice("How many items does the counter at the bottom of the list say are left?",
                         {"none_shown": "There is no counter, because the list is empty.", "1_item": "", "2_items": "", "3_items": "", "other": ""}),
}


def pick_action(a):
    """Compare what the model sees with the goal. Returns (action name, function) or (reason to stop, None)."""
    for i, todo in enumerate(TODOS):
        seen = a[f"has_{i}"]
        if seen.confidence < CUTOFF:
            return f"stop: not sure about '{todo}' ({seen.noul:.2f})", None
        if seen.noul < 0.5:
            return f"add '{todo}'", lambda page, t=todo: (page.fill(".new-todo", t), page.press(".new-todo", "Enter"))
    if a["first_done"].confidence < CUTOFF:
        return f"stop: not sure if '{DONE}' is completed", None
    if a["first_done"].noul < 0.5:
        return f"tick '{DONE}'", lambda page: page.locator("li", has_text=DONE).locator(".toggle").check()
    return "done", None


def run(page, on_step=None, max_steps=10):
    page.goto(URL)
    page.wait_for_selector(".new-todo")
    for step in range(1, max_steps + 1):
        shot = OUT / f"todo_{step:02d}.png"
        page.screenshot(path=str(shot))
        a, info = decide([media(shot, resolution="high")], QUESTIONS)
        name, act = pick_action(a)
        if on_step:
            on_step(step, a, name, info)
        if act is None:
            return name, step
        act(page)
        page.wait_for_timeout(300)
    return "gave up", max_steps


def print_step(step, a, name, info):
    seen = " ".join(f"{a[f'has_{i}'].noul:.2f}" for i in range(len(TODOS)))
    print(f"{step:<4} {seen:16} {a['first_done'].noul:6.2f} {a['items_left'].choice:11} {name:34} {info['ms']:>5}")


def main():
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless="--show" not in sys.argv)
        page = browser.new_page(viewport={"width": 1100, "height": 720})
        print(f"{'step':4} {'items seen':16} {'ticked':>6} {'counter':11} {'action':34} {'ms':>5}")
        result, steps = run(page, print_step)
        print(f"\nFinished with '{result}' after {steps} decision calls.")
        browser.close()


if __name__ == "__main__":
    main()
