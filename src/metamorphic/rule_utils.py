import os
import re

from openai import OpenAI


def util_functions_to_dict() -> dict:
    """
    :return: a dict with all functions defined in this module
    """
    return {'extract_float': extract_float,
            'currency': currency,
            'language': language}


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


def language(string: str):
    """
    returns the language of the given string
    :param string:
    :return:
    """
    prompt = f"""What is the language of the following text?: \n {string}. \n Return ENG for 
    English, ESP for Spanish, FR for French, GER for German and OTHER for other language."""
    response = call_openai(prompt)
    return response


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