"""Expense claims auditor.

Each claim has the amounts the employee typed in and a photo of the receipt.
Plain code checks the numbers against the policy. One Decisions API call per
claim checks what only the photo can show: is it a receipt, is it itemized,
is there alcohol on it, and does it match what the employee claimed.

    python audit.py
"""
import csv
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from decide import decide, media, text, yes_no

HERE = pathlib.Path(__file__).parent
CUTOFF = 0.80  # answers less confident than this go to a person

# The policy (policy.txt has the same rules in words)
TRIP = (datetime.date(2026, 11, 5), datetime.date(2026, 11, 9))
MEAL_LIMIT_PER_PERSON = 75.00
TIP_LIMIT = 0.20

QUESTIONS = {
    "is_receipt": yes_no("Is the image a receipt, bill or card payment slip from a restaurant, cafe or shop?"),
    "itemized": yes_no("Does the receipt list individual items with their prices?",
                       yes="Line items with prices are visible.", no="Only a total amount is shown, such as a card slip."),
    "has_alcohol": yes_no("Does the receipt include any alcoholic drinks, such as beer, wine or cocktails?"),
    "total_matches": yes_no("Is the total printed on the receipt the same amount as `total` in the claim?"),
    "date_matches": yes_no("Is the date printed on the receipt the same day as `date` in the claim?"),
    "merchant_matches": yes_no("Is the business name on the receipt the same as `merchant` in the claim?"),
}


def number_checks(claim):
    """Numbers and dates are compared in code, as the Decisions API docs recommend."""
    cuts = []
    date = datetime.date.fromisoformat(claim["date"])
    if not TRIP[0] <= date <= TRIP[1]:
        return "reject", "outside the trip dates", cuts
    if claim["tip"] > TIP_LIMIT * claim["subtotal"]:
        cuts.append(f"tip above {TIP_LIMIT:.0%}")
    if claim["subtotal"] / claim["employees"] > MEAL_LIMIT_PER_PERSON:
        cuts.append("above the meal limit")
    return None, None, cuts


def verdict(claim, a):
    """Plain code turns the answers into an action."""
    def unsure(key):
        return a[key].confidence < CUTOFF

    for key, why in (("is_receipt", "not a receipt"), ("itemized", "not itemized")):
        if unsure(key):
            return "review", f"unsure: {key}"
        if a[key].noul < 0.5:
            return "reject", why
    for key, why in (("total_matches", "total differs from the receipt"), ("date_matches", "date differs from the receipt"),
                     ("merchant_matches", "merchant differs from the receipt")):
        if unsure(key) or a[key].noul < 0.5:
            return "review", why
    action, why, cuts = number_checks(claim)
    if action:
        return action, why
    if unsure("has_alcohol"):
        return "review", "unsure: has_alcohol"
    if a["has_alcohol"].noul >= 0.5:
        cuts.insert(0, "alcohol")
    if cuts:
        return "approve in part", "remove: " + ", ".join(cuts)
    return "approve", "within policy"


def main():
    claims = json.loads((HERE / "claims.json").read_text())
    rows, total_usd = [], 0.0
    print(f"{'claim':5} {'receipt':24} {'action':16} {'why':34} {'ms':>5} {'tokens':>6}")
    for claim in claims:
        fields = {k: v for k, v in claim.items() if k not in ("id", "receipt")}
        answers, info = decide([text(json.dumps({"claim": fields}) + "\n"), media(HERE / "photos" / claim["receipt"], resolution="high")], QUESTIONS)
        action, why = verdict(claim, answers)
        total_usd += info["usd"]
        print(f"{claim['id']:5} {claim['receipt'][:-4]:24} {action:16} {why:34} {info['ms']:>5} {info['input_tokens']:>6}")
        rows.append({"claim": claim["id"], "receipt": claim["receipt"], "action": action, "why": why,
                     **{k: round(v.noul, 2) for k, v in answers.items()}, **info})
    with open(HERE / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} claims, {len(QUESTIONS)} checks each, ${total_usd:.5f} at the paid rate. Details in results.csv")


if __name__ == "__main__":
    main()
