import tiktoken

errors = []
conversation_name = ""
serial = ""
model = "gpt-4o-mini"
cost_ds_path = ''
test_name = ''
limit_cost = 10000000000
total_cost = 0
TOKENS = {
    "gpt-4o": {"input": 10**6/2.5, "output": 10**6/10},
    "gpt-4o-mini": {"input": 10**6/0.15, "output": 10**6/0.6},
    "whisper": 60/0.006,
    "tts-1": 1000/0.0015  # (characters, not tokens)
}

def count_tokens(text, model_used="gpt-4o-mini"):
    encoding = tiktoken.encoding_for_model(model_used)
    return len(encoding.encode(text))


def max_input_tokens_allowed(text, model_used):
    delta = limit_cost-total_cost
    limit_tokens = delta * TOKENS[model_used]["input"]
    input_tokens = count_tokens(text)

    if input_tokens > limit_tokens:
        return True
    else:
        return False

def max_output_tokens_allowed(model_used):
    delta = limit_cost-total_cost
    return delta * TOKENS[model_used]["output"]



default_context = ["never recreate a whole conversation, just act like you're a user or client",
                   "never generate a message starting by 'user:'",
                   'Sometimes, interact with what the assistant just said.',
                   'Never act as the assistant, always behave as a user.',
                   "Don't end the conversation until you've asked everything you need.",
                   "you're testing a chatbot, so there can be random values or irrational things "
                   "in your requests"
                   ]