import json
import re
import argparse
from llama_cpp import Llama, LlamaRAMCache, ChatCompletionMessage

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default="models/llama-model.gguf")
parser.add_argument("--tts", type=str, default="TTS", choices=['TTS', 'gtts', 'dummy'])
parser.add_argument("--input", type=str, default="whisper", choices=['input', 'whisper'])
parser.add_argument("--prompt", type=str, default="prompt.txt")
parser.add_argument("--n_threads_llm", type=int, default=6)
parser.add_argument("--n_threads_tts", type=int, default=8)
parser.add_argument("--n_context", type=int, default=4096)
parser.add_argument("--verbose", action='store_true')
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


llm = Llama(model_path=args.model, n_threads=args.n_threads_llm, n_ctx=args.n_context, n_gpu_layers=32, verbose=args.verbose)
#cache = LlamaRAMCache()
#llm.set_cache(cache)
file = open(args.prompt, "r")
prompt = file.read()
prompt_list = [
    ChatCompletionMessage(role='system', content=prompt),
    ChatCompletionMessage(role='user', content="Hello."),
]

matcher_acronym = re.compile(' *[A-Z]')
def estimate_token_count(prompt_list):
    count = 0
    for prompt in prompt_list:
        count += len(prompt['content'].split(' '))
    return count * 1.5

def trim_prompt_list(prompt_list):
    roles_dict = {}
    count = 0
    ret_list = []
    for prompt in prompt_list:
        if roles_dict.get(prompt['role']) == None:
            # reserve the first sentence of each role
            roles_dict[prompt['role']] = True
            count += len(prompt['content'].split(' '))
            ret_list.append(prompt)
        else:
            count += len(prompt['content'].split(' '))
            if count*1.5 > args.n_context/2:
                ret_list.append(prompt)
    print ("Trim prompt list")
    print ("From:")
    for p in prompt_list:
        print (f'    {p}')
    print ("To:")
    for p in ret_list:
        print (f'    {p}')
    return ret_list

while True:
    num_tokens = estimate_token_count(prompt_list)
    if num_tokens > 0.75 * args.n_context:
        prompt_list = trim_prompt_list(prompt_list)
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
    prev_content = ""
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
            if content in [',', ';', '.', '?', '!', '."', '?"', '!"', '\n', ':', ".'", "?'", "!'", '...']:
                if content != '.' or not matcher_acronym.match(prev_content):
                    speak_text(segment)
                    # For perf test and debug
                    #speak.wait()
                    segment = ""
            prev_content = content
        #print ("_", end="")
    if segment != "":
        speak_text(segment)
    speak.wait()

    print("")
    prompt_list.append(ChatCompletionMessage(role=role, content=answer))
    prompt = transcribe.transcribe('\nYou: ')
    prompt_list.append(ChatCompletionMessage(role='user', content=prompt))
    '''
    # code that start a new session after a while.
    prompt_list.append(ChatCompletionMessage(role='user', content="byebye."))
    prompt_list.append(ChatCompletionMessage(role='assistant', content="See you, have a nice day."))
    prompt_list.append(ChatCompletionMessage(role='system', content="You left the conversation, but several days later, you two met again."))
    prompt_list.append(ChatCompletionMessage(role='user', content="Hello."))
    '''
