from faster_whisper import WhisperModel

print("Loading the AI brain... please wait...")

# Load a lightweight, fast AI model that runs smoothly on your computer
model = WhisperModel("tiny", device="cpu", compute_type="int8")

print("AI Brain loaded successfully! Ready to listen.")