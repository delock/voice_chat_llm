import threading
import os
import time
import queue
from multiprocessing import Process, Queue, Value

omp_threads = 8

# sample rate must match model, tacotron2-DDC: 22050, jenny: 48000
#sample_rate=22050
sample_rate=48000
def loop_audio(audio_queue, done_flag):
    num_cpus = os.cpu_count()
    os.sched_setaffinity(0, range(num_cpus - omp_threads - 1, num_cpus - omp_threads))
    print(f'audio loop affinity = {os.sched_getaffinity(0)}')
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

def loop_speak(line_queue, audio_queue):
    num_cpus = os.cpu_count()
    os.sched_setaffinity(0, range(num_cpus - omp_threads, num_cpus))
    print(f'tts loop affinity = {os.sched_getaffinity(0)}')
    from TTS.api import TTS

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

os.environ['OMP_NUM_THREADS']=f'{omp_threads}'
audio_queue = Queue()
line_queue = Queue()
done_flag = Value('b', False)

p_audio = Process(target=loop_audio, args=(audio_queue, done_flag,))
p_tts = Process(target=loop_speak, args=(line_queue,audio_queue,))

p_audio.start()
p_tts.start()

