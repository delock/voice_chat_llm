import threading
from TTS.api import TTS
import sounddevice as sd
import pygame
import time
import queue


line_queue = queue.Queue()
audio_queue = queue.Queue()
line_q_idle = True
audio_q_idle = True

# sample rate must match model, tacotron2-DDC: 22050, jenny: 48000
#sample_rate=22050
sample_rate=48000
def loop_audio():
    global audio_q_idle
    while True:
        while audio_queue.empty():
            audio_q_idle = True
            time.sleep(0.001)

        audio_q_idle = False
        clip = audio_queue.get()

        duration = len(clip)/sample_rate
        sd.play(clip, sample_rate)
        time.sleep(duration)

def loop_speak():
    global line_q_idle
    while True:
        while line_queue.empty():
            line_q_idle = True
            time.sleep(0.001)

        line_q_idle = False
        line = line_queue.get()
        wav = tts.tts(line)
        audio_queue.put(wav)

def speak(line):
    global line_q_idle
    line_q_idle = False
    line_queue.put(line)

def wait():
    global line_q_idle
    global audio_q_idle
    while not line_q_idle or not audio_q_idle:
        time.sleep(0.001)

#tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
tts = TTS(model_name="tts_models/en/jenny/jenny", progress_bar=False, gpu=False)
# the line here is to 'pre-heat' audio in the system, otherwise the first word cannot be heard
pygame.mixer.init()
thread_speak = threading.Thread(target=loop_speak)
thread_audio = threading.Thread(target=loop_audio)
thread_speak.start()
thread_audio.start()

