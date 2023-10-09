import threading
from gtts import gTTS
from io import BytesIO
import pygame
import time
import queue


line_queue = queue.Queue()
audio_queue = queue.Queue()
line_q_idle = True
audio_q_idle = True

def loop_audio():
    global audio_q_idle
    while True:
        while audio_queue.empty():
            audio_q_idle = True
            time.sleep(0.001)

        audio_q_idle = False
        clip = audio_queue.get()

        clip.seek(0)
        pygame.mixer.music.load(clip)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

def loop_speak():
    global line_q_idle
    while True:
        while line_queue.empty():
            line_q_idle = True
            time.sleep(0.001)

        line_q_idle = False
        line = line_queue.get()
        mp3_fp = BytesIO()
        tts = gTTS(line, lang='en')
        tts.write_to_fp(mp3_fp)
        audio_queue.put(mp3_fp)

def speak(line):
    global line_q_idle
    line_q_idle = False
    line_queue.put(line)

def wait():
    global line_q_idle
    global audio_q_idle
    while not line_q_idle or not audio_q_idle:
        time.sleep(0.001)

pygame.mixer.init()
thread_speak = threading.Thread(target=loop_speak)
thread_audio = threading.Thread(target=loop_audio)
thread_speak.start()
thread_audio.start()

