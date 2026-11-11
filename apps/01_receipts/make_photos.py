"""Generate realistic receipt photos with a Gemini image model. The photos are already in photos/.

    python make_photos.py            # all receipts
    python make_photos.py 02         # only names that start with 02
"""
import base64, json, os, pathlib, sys, urllib.request, urllib.error

MODEL = os.environ.get("IMAGE_MODEL", "gemini-nano-banana-2.1")
OUT = pathlib.Path(__file__).parent / "photos"
STYLE = ("A realistic smartphone photo, taken from above at a slight angle, of a single printed thermal paper receipt lying on {surface}. "
         "Natural indoor light, soft shadow, slightly curled paper, sharp and fully legible black text, the whole receipt in frame. "
         "Every price sits on the same line as its label, in one right-aligned column. "
         "The receipt must show exactly this text, line by line, with nothing added:\n\n{text}")

RECEIPTS = {
    "01_team_lunch": ("a white marble cafe table next to a coffee cup, photographed straight from above", """GREEN FORK CAFE
88 Market St, San Diego CA
Date: 11/06/2026  12:48 PM
Guests: 2
2 Chicken bowl ...... 29.00
1 Sparkling water ...  4.50
1 Iced tea ..........  4.50
Subtotal ............ 38.00
Tax .................  2.95
Tip .................  5.70
TOTAL ............... 46.65
VISA ****4417
Thank you!"""),
    "02_client_dinner": ("a dark restaurant table next to a folded napkin", """HARBOR GRILL
412 Pier Ave, San Diego CA
Date: 11/08/2026  8:42 PM
Guests: 2
1 Grilled salmon    28.00
1 Ribeye steak      41.00
2 Draft beer        16.00
1 Glass pinot noir  14.00
1 Cheesecake         9.00
Subtotal           108.00
Tax                  8.37
Tip                 35.00
TOTAL              151.37
VISA ****4417"""),
    "03_after_the_trip": ("a white kitchen counter", """SUNSET TACOS
19 Ocean Blvd, San Diego CA
Date: 11/14/2026  7:05 PM
Guests: 2
4 Fish taco         22.00
2 Horchata           8.00
Subtotal            30.00
Tax                  2.33
Tip                  4.50
TOTAL               36.83
VISA ****4417"""),
    "04_steakhouse": ("a black leather bill folder on a white tablecloth", """PRIME 1887 STEAKHOUSE
700 Broadway, San Diego CA
Date: 11/07/2026  7:30 PM
Guests: 2
2 Wagyu tasting menu 196.00
1 Truffle fries       16.00
2 Sparkling water     12.00
Subtotal             224.00
Tax                   17.36
Tip                   40.00
TOTAL                281.36
AMEX ****1009"""),
    "05_card_slip_only": ("a grey office desk next to a pen", """LA PLAYA BISTRO
CARDHOLDER COPY
Date: 11/07/2026  1:15 PM
Terminal 03  Auth 77120
AMOUNT          USD 96.40
VISA ****4417  APPROVED"""),
}
EXTRA = {
    "06_not_a_receipt": "A realistic smartphone photo of a paper boarding pass and a hotel key card lying on a grey office desk. No receipt, no prices.",
}


def generate(prompt):
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "3:4"}}}
    req = urllib.request.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent", data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        for part in json.loads(r.read())["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                return part["inlineData"]["mimeType"], base64.b64decode(part["inlineData"]["data"])
    raise RuntimeError("no image in the response")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    only = sys.argv[1:] or [""]
    jobs = {n: STYLE.format(surface=s, text=t) for n, (s, t) in RECEIPTS.items()} | EXTRA
    for name, prompt in jobs.items():
        if not any(name.startswith(o) for o in only):
            continue
        try:
            mime, data = generate(prompt)
        except urllib.error.HTTPError as e:
            print(name, "ERROR", e.code, e.read()[:300]); continue
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(mime, ".png")
        (OUT / (name + ext)).write_bytes(data)
        print(name, mime, len(data), "bytes")
