# App 2: screen checks for a browser agent

A small agent completes a checkout form by looking at screenshots. At each step it sends one screenshot with five questions, and plain code picks the action from the answers.

```bash
pip install playwright
python agent.py          # headless, uses your installed Chrome
python agent.py --show   # watch the browser
python live_todo.py      # the same loop on a live demo site
```

- **Small checks, combined in code:** "Is a cookie banner visible?", "Is an email error visible?", "Is the card field empty?", "Is the button enabled?", plus which screen it's on. `RULES` in `agent.py` sets the order.
- **Criteria matter:** the card field shows grey example digits. Without a description of what "empty" means, the model reads them as a filled field. The two descriptions on `card_empty` fix that.
- **Resolution matters for small details:** screenshots go in at `high` resolution. At `medium`, the empty-field check fell below the cutoff on a larger window, and the agent stopped.
- **It stops when unsure:** if a check it needs is below 0.80, the agent stops for a person.

- **It works on a page it wasn't built for:** `live_todo.py` runs the same loop on Playwright's public TodoMVC demo. It adds three to-dos and ticks one, checking the page after every action.

Screenshots of every step land in `out/`. The page is `shop/index.html`; change it to try other states.
