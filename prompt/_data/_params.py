
completion_default_params = {
    "model": "text-davinci-003",
    "suffix": "[/]",
    "max_tokens":  64,
    "temperature": 1,
    "top_p": 1,
    "n": 1,
    "stream": False,
    "logprobs": None,
    "echo": False,
    "stop": None,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "best_of": 1,
    "logit_bias": {},
    "user": "Debug"
}

chat_completion_default_params = {
    "model": "gpt-3.5-turbo",
    "messages": [
        {"role": "system", "content": "You are ChatGPT, a helpful AI language model."},
    ],
    "max_tokens": 64,
    "temperature": 1,
    "top_p": 1,
    "n": 1,
    "stream": False,
    "stop": None,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "logit_bias": {},
    "user": "Debug"
}