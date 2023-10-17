import re
import sounddevice as sd
from whispercpp import Whisper

fs = 16000
seconds = 10


w = Whisper.from_pretrained("models/ggml-base.en.bin")
#iterator = w.stream_transcribe(length_ms=5000, device_id=2, num_proc=6)
def transcribe(prompt):
    sentence = ""
    try:
        #for it in iterator:
        #    sentence=sentence+it
        print (f"{prompt}", end='', flush=True)
        recording = sd.rec(int(seconds*fs), samplerate=fs, channels=1)
        sd.wait()
    finally:
        sentence = w.transcribe(recording)
        clean_sentence = re.sub(r"\([^(]*\)", "", sentence)
        print (f"{clean_sentence}")
        return clean_sentence
