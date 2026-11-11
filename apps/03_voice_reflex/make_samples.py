"""Regenerate the sample caller clips with Gemini text-to-speech. The .wav files are already in samples/."""
import base64, json, os, pathlib, subprocess, urllib.request

OUT = pathlib.Path(__file__).parent / "samples"
URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts:generateContent"
CLIPS = {
    "01_opening_hours": ("Kore", "Say in a friendly, relaxed voice: Hi, I was just wondering what time you open on Saturday."),
    "02_wants_a_person": ("Charon", "Say in an annoyed, raised voice: This is the third time I am calling. I am done with the bot. Get me a real person right now."),
    "03_still_talking": ("Kore", "Say slowly, hesitating, and trail off without finishing the sentence: Yeah, so my order number is, um, hold on, let me find it, it's"),
    "04_goodbye": ("Puck", "Say in a cheerful voice: Okay perfect, that's everything I needed. Thanks, bye."),
    "05_refund_then_person": ("Charon", "Say in a tired, slightly frustrated voice: Hi, yes, I got the email about my refund, and I checked my bank statement this morning, and nothing has arrived. Honestly, can I just talk to a real person about this?"),
}

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, (voice, prompt) in CLIPS.items():
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
        req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            part = json.loads(r.read())["candidates"][0]["content"]["parts"][0]["inlineData"]
        raw = OUT / f"{name}.raw.wav"
        raw.write_bytes(base64.b64decode(part["data"]))
        # 16 kHz mono keeps the files small (afconvert ships with macOS)
        subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16@16000", "-c", "1", str(raw), str(OUT / f"{name}.wav")], check=True)
        raw.unlink()
        print(name, part["mimeType"], (OUT / f"{name}.wav").stat().st_size, "bytes")
