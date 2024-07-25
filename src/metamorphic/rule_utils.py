import re


def util_functions_to_dict() -> dict:
    """
    :return: a dict with all functions defined in this module
    """
    return {'extract_float': extract_float,
            'currency' : currency}


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


def currency_name(string):
    pattern = r'\b(dollars|euros|pounds|yen|rupees)\b'
    map_currency = {'dollars': 'USD', 'euros': 'EUR', 'pounds': 'GBP', 'yen': 'JPY', 'rupees': 'INR'}
    match = re.search(pattern, string, re.IGNORECASE)

    if match:
        return map_currency[match.group()]
    else:
        return None
