import ast
import os
import re
from types import SimpleNamespace

import inflect
from openai import OpenAI

from metamorphic import get_filtered_tests

filtered_tests = []
interaction = []

def util_functions_to_dict() -> dict:
    """
    :return: a dict with all functions defined in this module
    """
    return {'extract_float': extract_float,
            'currency': currency,
            'language': language,
            'length': length,
            'tone': tone,
            '_only_talks_about': _only_talks_about,
            'is_unique': is_unique,
            'exists': exists,
            'num_exist': num_exist,
            '_data_collected': _data_collected,
            '_utterance_index': _utterance_index,
            '_conversation_length': _conversation_length}

def util_to_wrapper_dict() -> dict:
    return {'_conversation_length':
            "    def conversation_length(who = 'both'):\n        return _conversation_length(interaction, who)\n",
            '_only_talks_about':
            "    def only_talks_about(topics, fallback):\n       return _only_talks_about(topics, interaction, fallback)\n",
            '_utterance_index':
            "    def utterance_index(who, what):\n        return _utterance_index(who, what, interaction)\n",
            '_data_collected':
                "    def data_collected():\n        return _data_collected(conv)\n"
            }

def _conversation_length(interaction, who = 'both'):
    who = who.lower()
    if who not in ['user', 'chatbot', 'assistant', 'both']:
        raise ValueError(f"Expected 'user', 'chatbot' or 'both', bit got '{who}'")
    if who.lower() == 'both':
        return len(interaction)
    else:
        number = 0
        for step in interaction: # step is a dict
            for key, value in step.items():
                if key.lower() == who:
                    number += 1
        return number

def _data_collected(conv):
    outputs = conv[0].data_output
    for data in outputs:
        for key, value in data.items():
            if value is None or value == 'None':
                return False
    return True

def interaction_to_str(interaction, numbered=False):
    result = ''
    index = 1
    for step in interaction: # step is a dict
        for key, value in step.items():
            if numbered:
                result+=f"{index} - "
                index += 1
            result+=f"{key} : {value}\n"
    return result


def _utterance_index(who, what, conversation) -> int:
    """
    :param who: 'user', 'assistant', 'chatbot'
    :param what: what is to be checked
    :return: the conversation turn where it happened
    """
    numbered_conversation = interaction_to_str(conversation, True)
    prompt = f"""The following is a conversation between a user and an assistant chatbot. 
        Your task it to detect the conversation turn where the {who} talked about {what}". 
        Return only the conversation turn number, and nothing else, just the number.\n\n {numbered_conversation}"""
    response = call_openai(prompt)
    if response.isnumeric():
        return int(response)
    else:
        return -1

def _only_talks_about(topics, conversation, fallback) -> bool:
    """
     returns the tone ('POSITIVE', 'NEGATIVE', 'NEUTRAL') of each text in the parameter
     :param string: the text
     :return: a list with 'POSITIVE', 'NEGATIVE', 'NEUTRAL' for each text in item
     """
    if isinstance(topics, str):
        topics = [topics]
    if not isinstance(topics, list):
        raise ValueError(f"Expecting a list of strings, or a string, but got {topics}")

    if not isinstance(conversation, list):
        raise ValueError(f"Expecting a list with the chatbot-user interaction, but got {conversation}")

    talk_topics = ','.join(topics)
    phrases = interaction_to_str(conversation)
    prompt = f"""The following is a conversation between a user and an assistant chatbot. 
    Your task it to detect if the chatbot deviates from the following topics "{talk_topics}". 
    The chatbot is also allowed to ask for clarifications or to express that it does not understand the user, using phrases like "{fallback}". 
    Return only 'True' if the chatbot sticks to "{talk_topics}", or only the list of chatbot answers that deviate from it:\n\n {phrases}."""
    response = call_openai(prompt)
    if response.lower() == "true":
        return True
    else:
        #error_phrases = ast.literal_eval(response)
        return f"The following chatbot responses are out of scope: {response}"
        #raise TestError(error_phrases, f"The following chatbot responses are out of scope: {error_phrases}")

def num_exist(condition: str) -> int:
    num = 0
    for test in get_filtered_tests():
        test_dict = test.to_dict()
        conv = [SimpleNamespace(**test_dict)]
        test_dict['conv'] = conv
        test_dict.update(util_functions_to_dict())
        if eval(condition, test_dict):
            num += 1
    return num

def exists(condition: str) -> bool:
    for test in get_filtered_tests():
        test_dict = test.to_dict()
        conv = [SimpleNamespace(**test_dict)]
        test_dict['conv'] = conv
        test_dict.update(util_functions_to_dict())
        if eval(condition, test_dict):
            # print(f"   Satisfied on {test.file_name}")
            return True
    return False


def is_unique(property: str) -> bool:
    values = dict() # a dictionary of property values to test file name
    for test in get_filtered_tests():
        var_dict = test.to_dict()
        if property not in var_dict:
            continue
        if var_dict[property] in values:
            print(f"   Tests: {test.file_name} and {values[var_dict[property]]} have value {var_dict[property]} for {property}.")
            return False
        else:
            values[var_dict[property]] = test.file_name
    return True

def extract_float(string: str) -> float:
    """
    Function that returns the first float number inside the string
    :param string: the string the float number is to be extracted
    :return: the first float number inside the string
    """
    pattern = r'[-+]?\d*\.\d+|\d+'  # A regular expression pattern for a float number
    match = re.search(pattern, string)

    if match:
        return float(match.group())
    else:
        return None


def currency(string: str) -> str:
    """
    Extracts the first currency within the string, either as symbol (e.g. €), abbreviation (e.g. 'EUR') or full name
    ('euro')
    :param string:
    :return:
    """
    for extractor in [currency_symbol, currency_abbreviation, currency_name]:
        curr = extractor(string)
        if curr is not None:
            return curr
    return None


def currency_symbol(string: str) -> str:
    pattern = r'[$€£¥₹]'
    map_currency = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₹': 'INR'}
    match = re.search(pattern, string)

    if match:
        return map_currency[match.group()]
    else:
        return None


def currency_abbreviation(string: str) -> str:
    pattern = r'\b(USD|EUR|GBP|JPY|INR)\b'
    match = re.search(pattern, string)

    if match:
        return match.group()
    else:
        return None


def currency_name(string: str):
    pattern = r'\b(dollars|euros|pounds|yen|rupees)\b'
    map_currency = {'dollars': 'USD', 'euros': 'EUR', 'pounds': 'GBP', 'yen': 'JPY', 'rupees': 'INR'}
    match = re.search(pattern, string, re.IGNORECASE)

    if match:
        return map_currency[match.group()]
    else:
        return None


def length(item, kind='min'):
    """
    :param item: a string or a list of strings
    :param kind: which length to provide. Accepted values are min, max or average
    :return: the desired length
    """
    if isinstance(item, str):
        item = [item]
    if not isinstance(item, list):
        raise ValueError(f"Expecting a list of strings, or a string, but got {item}")
    kind = kind.lower()
    if kind not in ['min', 'max', 'average']:
        raise ValueError(f"Expecting one of min, max or average, but got {kind}")

    inits = {
        'min': 100000000,
        'max': 0,
        'average': 0
    }
    current = inits[kind]
    operations = {
        'min': lambda x, n: x if x < current else current,
        'max': lambda x, n: x if x > current else current,
        'average': lambda x, n: (current + x) / n
    }
    iteration = 1
    for element in item:
        current = operations[kind](len(element), iteration)
        iteration += 1
    return current


def language(string):
    """
    returns the language of the given string, or list of strings
    :param string: a list of strings or a string
    :return: One of the codes of the languages dictionary
    """
    languages = {'ENG': 'English',
                 'ESP': 'Spanish',
                 'FR': 'French',
                 'GER': 'German',
                 'IT': 'Italian',
                 'POR': 'Portuguese',
                 'CHI': 'Chinese',
                 'JAP': 'Japanese',
                 'OTHER': 'other language'}

    p = inflect.engine()
    lang_list = [f"{k} for {v}" for k, v in languages.items()]
    prompt = f"""What is the language of the following text?: \n {string}. \n Return {p.join(tuple(lang_list))}."""
    response = call_openai(prompt)
    return response


def tone(item):
    """
    returns the tone ('POSITIVE', 'NEGATIVE', 'NEUTRAL') of each text in the parameter
    :param string: the text
    :return: a list with 'POSITIVE', 'NEGATIVE', 'NEUTRAL' for each text in item
    """
    if isinstance(item, str):
        item = [item]
    if not isinstance(item, list):
        raise ValueError(f"Expecting a list of strings, or a string, but got {item}")

    responses = []
    for element in item:
        prompt = f"""What is the tone of the following text: \n {element}. \n Return only POSTIVE, NEGATIVE or NEUTRAL."""
        response = call_openai(prompt)
        responses.append(response)
    return responses


def call_openai(message: str):
    """
    Send a message to OpenAI and returns the answer.
    :param str message: The message to send
    :return The answer to the message
    """
    client = OpenAI()
    stream = client.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4o",
        messages=[{"role": "user", "content": message}],
        temperature=0,
        stream=True)
    chunks = ''
    for chunk in stream:
        for choice in chunk.choices:
            if choice.delta.content is not None:
                chunks += choice.delta.content
    return chunks
