import json
import argparse
from llama_cpp import Llama, LlamaRAMCache, ChatCompletionMessage

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="models/llama-model.gguf")
parser.add_argument("--tts", type=str, default="TTS")
parser.add_argument("--input", type=str, default="input")
parser.add_argument("--prompt", type=str, default="prompt.txt")
args = parser.parse_args()

if args.tts == "TTS":
    import speak_TTS as speak
if args.tts == "gtts":
    import speak_gtts as speak
if args.tts == "dummy":
    import speak_dummy as speak

if args.input == "input":
    import transcribe_input as transcribe
if args.input == "whisper":
    import transcribe_whisper as transcribe

import re
from cleantext import clean
def speak_text(line):
    #post processing
    line = re.sub(r"\*[a-zA-Z 0-9]*\*", "", line)
    line = clean(line, no_emoji=True)

    if line != "":
        speak.speak(line)


llm = Llama(model_path=args.model, n_threads=6, verbose=False)
#cache = LlamaRAMCache()
#llm.set_cache(cache)
file = open(args.prompt, "r")
prompt = file.read()
prompt_list = [
    ChatCompletionMessage(role='system', content=prompt),
    ChatCompletionMessage(role='user', content="Hello."),
]
while True:
    #print (prompt_list)
    stream = llm.create_chat_completion(
        prompt_list,
        max_tokens=4096,
        stream=True,
        stop=[],
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        repeat_penalty=1.1,

    )
    role = None
    answer = ""
    segment = ""
    print('\nTeacher: ', end='')
    for output in stream:
        if 'role' in output["choices"][0]['delta']:
            role = output["choices"][0]['delta']['role']
            #print (f'\nchange role to {role}\n')
        if 'content' in output["choices"][0]['delta']:
            content = output["choices"][0]['delta']['content']
            print(content, end='', flush=True)
            answer = answer + content
            segment = segment + content
            if content in ['.', '?', '!']:
                speak_text(segment)
                # For perf test and debug
                #speak.wait()
                segment = ""
    if segment != "":
        speak_text(segment)
    speak.wait()

    print("")
    prompt_list.append(ChatCompletionMessage(role=role, content=answer))
    prompt = transcribe.transcribe('\nYou: ')
    prompt_list.append(ChatCompletionMessage(role='user', content=prompt))
