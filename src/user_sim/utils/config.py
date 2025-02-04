import tiktoken

errors = []
conversation_name = ""
serial = ""
model = "gpt-4o-mini"
cost_ds_path = ''
test_name = ''

# cost metrics
token_count_enabled = False
limit_cost = 10000000000
limit_individual_cost = 10000000000
total_cost = 0
total_individual_cost = 0



# def count_tokens(text, model_used="gpt-4o-mini"):
#     encoding = tiktoken.encoding_for_model(model_used)
#     return len(encoding.encode(text))



default_context = ["never recreate a whole conversation, just act like you're a user or client",
                   "never generate a message starting by 'user:'",
                   'Sometimes, interact with what the assistant just said.',
                   'Never act as the assistant, always behave as a user.',
                   "Don't end the conversation until you've asked everything you need.",
                   "you're testing a chatbot, so there can be random values or irrational things "
                   "in your requests"
                   ]