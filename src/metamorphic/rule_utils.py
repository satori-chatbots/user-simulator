import os
import re
from metamorphic import filtered_tests
import inflect
from openai import OpenAI

from metamorphic.tests import Test


def util_functions_to_dict() -> dict:
    """
    :return: a dict with all functions defined in this module
    """
    return {'extract_float': extract_float,
            'currency': currency,
            'language': language,
            'length': length,
            'tone': tone,
            'is_unique': is_unique}

def is_unique(property: str) -> bool:
    values = dict() # a dictionary of property values to test file name
    for test in filtered_tests:
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
