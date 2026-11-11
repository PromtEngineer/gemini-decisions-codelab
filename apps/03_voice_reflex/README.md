# App 3: voice agent reflexes

A voice agent has to decide fast: has the caller finished, do they want a person, are they getting frustrated? These scripts ask those questions on the audio itself, with no transcription step.

```bash
python reflex.py                 # all five sample clips
python reflex.py my_clip.wav     # your own recording
python stream.py                 # replay a clip one second at a time
python takes.py my_clips/        # flag restarts in your own narration clips
```

- **`reflex.py`** sends each clip with four questions and prints the action: answer, keep listening, hand off to a person, or say goodbye.
- **`stream.py`** replays a clip as if it were arriving live and asks after every second, so you can see when the hand-off would fire and how the frustration score moves.

- **`takes.py`** is a second use of the same idea: point it at clips from your own narration recording, and it flags the ones where you stumble and restart a phrase.

The sample clips are synthetic speech from Gemini text-to-speech (`make_samples.py`). For turn-taking in a real product, pair these checks with silence detection.
