import threading
from TTS.api import TTS
import time
import queue
from multiprocessing import Process, Queue, Value


line_queue = Queue()
done_flag = Value('b', False)
audio_queue = queue.Queue()

# sample rate must match model, tacotron2-DDC: 22050, jenny: 48000
#sample_rate=22050
sample_rate=48000
def loop_audio(done_flag):
    import sounddevice as sd
    import pygame
    # the line here is to 'pre-heat' audio in the system, otherwise the first word cannot be heard
    pygame.mixer.init()
    while True:
        while audio_queue.empty():
            time.sleep(0.001)

        clip = audio_queue.get()

        if clip != []:
            duration = len(clip)/sample_rate
            sd.play(clip, sample_rate)
            time.sleep(duration)
        else:
            # when the element in queue is [], means user had finished all TTS
            # request and waiting for all audio clip finishes
            done_flag.value = True

def loop_speak(line_queue, done_flag):
    thread_audio = threading.Thread(target=loop_audio, args=(done_flag,))
    thread_audio.start()

    #tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
    tts = TTS(model_name="tts_models/en/jenny/jenny", progress_bar=False, gpu=False)

    while True:
        while line_queue.empty():
            time.sleep(0.001)

        line = line_queue.get()
        if line != []:
            wav = tts.tts(line)
            audio_queue.put(wav)
        else:
            audio_queue.put([])


def speak(line):
    done_flag.value = False
    line_queue.put(line)

def wait():
    line_queue.put([])
    # wait until done_flag set to False
    while done_flag.value == False:
        time.sleep(0.001)

p = Process(target=loop_speak, args=(line_queue,done_flag))
p.start()

