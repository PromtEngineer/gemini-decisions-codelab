# Gemini Decisions API: quickstart and codelab

The Gemini Decisions API answers closed questions about your input: yes or no, one option from a list, or a level on a rubric. It returns probabilities and a confidence score, and it never generates text. The model is `gemini-decision-1`.

This repo has a quickstart, a notebook that walks through every feature, and three small apps.

> This is a personal, unofficial project. It isn't a Google product or official documentation. The official guide is at [aistudio.google.com/docs/decisions-api](https://aistudio.google.com/docs/decisions-api).

## Quickstart

1. Get an API key from [Google AI Studio](https://aistudio.google.com/api-keys). The free tier is enough for everything here.

2. Install the SDK (version 3.2 or later) and set your key:

   ```bash
   pip install -U "google-genai>=3.2"
   export GEMINI_API_KEY=your-key
   ```

3. Make your first call:

   ```python
   from google import genai

   client = genai.Client(http_options={"api_version": "v1beta"})

   result = client.decisions.create(
       model="gemini-decision-1",
       input="The blue mug I ordered on Monday arrived cracked on Wednesday.",
       questions={
           "is_damaged": {"type": "noul", "instructions": "Did the item arrive damaged?"},
           "queue": {
               "type": "choice",
               "instructions": "Which support queue should handle this message?",
               "criteria": {
                   "billing": "Payment, invoice, or refund questions.",
                   "replacements": "Damaged, missing, or wrong items.",
                   "general": "Product questions and account updates.",
               },
           },
       },
   )

   damaged = result.answers["is_damaged"]
   queue = result.answers["queue"]
   print(f"P(damaged)={damaged.noul:.2f}  queue={queue.choice}  confidence={queue.confidence:.2f}")
   ```

4. Act on the confidence:

   ```python
   if queue.confidence >= 0.8:
       route_to(queue.choice)
   else:
       route_to("human_review")
   ```

## The three question types

| Type | Use it to | You get back |
|---|---|---|
| `noul` | Check whether a statement holds | The probability of yes |
| `choice` | Pick one option from a list (2 to 255) | The top option and a probability for every option |
| `score` | Rate the input on ordered levels | A score between levels and a probability for every level |

One request takes one shared input (text, images, audio, video, PDF, or a mix) and up to 1,000 questions.

## The codelab notebook

[`Gemini_Decision_1_Codelab.ipynb`](Gemini_Decision_1_Codelab.ipynb) runs in Colab or locally. It covers:

- All three question types, and using confidence to act or escalate
- Many questions on one input, and how tokens are counted
- Images, audio, video and PDFs
- The use cases from Google's launch post: tool selection, model routing, context grading, an emoji picker and a safety check for tool outputs
- Four habits from the docs that keep answers reliable
- What a call costs

Every cell uses public sample files, so it needs nothing but your key.

## The apps

| App | What it does | Run it |
|---|---|---|
| [`apps/01_receipts`](apps/01_receipts) | Audits expense claims against their receipt photos | `python apps/01_receipts/audit.py` |
| [`apps/02_screen_checks`](apps/02_screen_checks) | A browser agent that reads each screen with one decision call | `python apps/02_screen_checks/agent.py` |
| [`apps/03_voice_reflex`](apps/03_voice_reflex) | Decides when a voice agent should answer, wait or hand off, from audio alone | `python apps/03_voice_reflex/reflex.py` |

`decide.py` holds the helpers the apps share. App 2 also needs `pip install playwright` and Google Chrome.

## Habits that keep answers reliable

These follow the best practices in the official guide.

- **Ask small, single-purpose questions** and combine the answers in code.
- **Describe your options.** Add `criteria` when a question could be read two ways.
- **Give a `choice` a way out.** Add an option such as `other`, or ask a separate yes/no question about scope. A `choice` always picks one of your options, even when none fits.
- **Send only what the questions need.** Unrelated content in the input can sway an answer.
- **Do arithmetic in code.** Compare numbers, dates and durations yourself and pass the result as a named fact.
- **Set your cutoff from your own data,** and send answers below it to a person or a bigger model.
- **Treat input as untrusted.** Keep a second check on actions that matter.

## Limits and price

| | |
|---|---|
| Questions per request | 1 to 1,000 |
| Options per `choice` | 2 to 255 |
| Context window | 262,144 tokens across the input and all questions |
| Price | $0.10 per 1 million input tokens on the paid tier. Output tokens are always 0 |
| Free tier | 200 requests a minute, 50,000 tokens a minute, 10,000 requests a day |

The API doesn't generate explanations, and it doesn't support context caching or the Batch API. Check the [pricing](https://aistudio.google.com/docs/pricing) and [rate limits](https://aistudio.google.com/docs/rate-limits) pages for current values.
