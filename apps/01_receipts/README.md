# App 1: expense claims auditor

Each claim in `claims.json` has the amounts an employee typed in and a photo of the receipt. The script decides whether to approve, approve in part, reject, or send the claim to a person.

- **Code checks the numbers:** trip dates, the 20% tip limit and the $75 meal limit. The Decisions API docs recommend comparing numbers and dates in code.
- **The call gets only the claim and the photo:** an earlier version also sent the whole policy, and that swayed an unrelated answer. On a receipt dated outside the trip, the model said a 15% tip was above 20%.
- **One decision call checks the photo:** is it a receipt, is it itemized, is there alcohol on it, and do the total, date and merchant match the claim.
- **Confidence decides who handles it:** any answer below 0.80 sends the claim to review.

```bash
python audit.py
```

The seven sample claims cover a clean lunch, a dinner with alcohol and a large tip, a meal after the trip, a meal above the limit, a card slip with no items, a photo that isn't a receipt, and a claim whose total doesn't match its receipt. All receipts are made up. The photos in `photos/` were generated with a Gemini image model (`make_photos.py`).

To use your own data, add receipt photos to `photos/` and rows to `claims.json`, then edit the limits at the top of `audit.py`.
