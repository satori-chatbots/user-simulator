import os

import pandas as pd
import yaml
import json
import configparser
from datetime import datetime, timedelta
import re
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import importlib.util
from .exceptions import *
from openai import OpenAI
from user_sim.utils.config import errors
import logging
logger = logging.getLogger('Info Logger')


def check_keys(key_list: list):
    if os.path.exists("keys.properties"):
        logger.info("properties found!")
        config = configparser.ConfigParser()
        config.read('keys.properties')

        # Loop over all keys and values
        for key in config['keys']:
            key = key.upper()
            os.environ[key] = config['keys'][key]

    for k in key_list:
        if not os.environ.get(k):
            raise Exception(f"{k} not found")


check_keys(["OPENAI_API_KEY"])
client = OpenAI()


def save_json(msg, test_name, path):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(path, f'{test_name}_{timestamp}.json')
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(msg, file, indent=4)


def str_to_bool(s):
    if s.lower() in ['true', '1', 'yes', 'y']:
        return True
    elif s.lower() in ['false', '0', 'no', 'n']:
        return False
    else:
        raise ValueError(f"Cannot convert {s} to boolean")


def execute_list_function(path, function_name, arguments=None):
    spec = importlib.util.spec_from_file_location("my_module", path)
    my_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(my_module)

    function_to_execute = getattr(my_module, function_name)

    if arguments:

        if not isinstance(arguments, list):
            arguments = [arguments]

        args = [item for item in arguments if not isinstance(item, dict)]
        dict_list = [item for item in arguments if isinstance(item, dict)]
        kwargs = {k: v for dic in dict_list for k, v in dic.items()}

        try:
            result = function_to_execute(*args, **kwargs)
        except TypeError as e:
            raise InvalidFormat(f"No arguments needed for this function: {e}")

    else:
        try:
            result = function_to_execute()
        except TypeError as e:
            raise InvalidFormat(f"Arguments are needed for this function: {e}")

    return result


def list_to_phrase(s_list: list, prompted=False):  # todo: cambiar a list_to_askabout
    # s_list: list of strings
    # l_string: string values extracted from s_list in string format
    l_string = s_list[0]

    if len(s_list) <= 1:
        return f"{s_list[0]}"
    else:
        for i in range(len(s_list) - 1):
            if s_list[i + 1] == s_list[-1]:
                l_string = f" {l_string} or {s_list[i + 1]}"
            else:
                l_string = f" {l_string}, {s_list[i + 1]}"

    if prompted:
        l_string = "please, ask about" + l_string

    return l_string


def read_yaml(file):
    with open(file, 'r', encoding="UTF-8") as f:
        yam_file = yaml.safe_load(f)
    return yam_file


def generate_serial():
    now = datetime.now()
    # serial = datetime.now().strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}"
    serial = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return serial


class MyDumper(yaml.Dumper):
    def write_line_break(self, data=None):
        super().write_line_break(data)
        super().write_line_break(data)


def get_time_stats(response_time):

    times = pd.to_timedelta(response_time)

    time_report = {
        'average': str(times.mean()).split("days")[-1].strip(),
        'max': str(times.max()).split("days")[-1].strip(),
        'min': str(times.min()).split("days")[-1].strip()
    }
    return time_report


def save_test_conv(history, metadata, test_name, path, serial, conversation_time, response_time, av_data, counter):
    print("Saving conversation...")

    cr_time = {'conversation time': conversation_time,
               'assistant response time': response_time,
               "response time report": get_time_stats(response_time)}

    path_folder = path + f"/{test_name}"
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    data = [metadata, cr_time, history]
    test_folder = path_folder + f"/{serial}"

    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    file_path_yaml = os.path.join(test_folder, f'{counter}_{test_name}_{serial}.yml')
    file_path_csv = os.path.join(test_folder, f'{counter}_{test_name}_{serial}.csv')

    with open(file_path_yaml, "w", encoding="UTF-8") as archivo:
        yaml.dump_all(data, archivo, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if av_data[1]:
        av_data[0].to_csv(file_path_csv, index=True, sep=';', header=True, columns=['verification', 'data'])

    print(f"Conversation saved in {path}")
    print('------------------------------')
    errors.clear()


def preprocess_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Eliminar signos de puntuación
    text = re.sub(r'[^\w\s]', '', text)
    return text


def str_to_bool(s):
    return {'true': True, 'false': False}[s.lower()]


def nlp_processor(msg, patterns=None, threshold=0.5):
    read_patterns = [patterns]

    prepro_patterns = [preprocess_text(pattern) for pattern in read_patterns]

    vectorizer = TfidfVectorizer().fit(prepro_patterns)

    processed_msg = preprocess_text(msg)

    # Vectorizar el mensaje y los patrones de fallback
    vectors = vectorizer.transform([processed_msg] + prepro_patterns)
    vector_msg = vectors[0]
    patt_msg = vectors[1:]

    # Calcular similitud de coseno
    similarities = cosine_similarity(vector_msg, patt_msg)
    max_sim = similarities.max()

    # Definir un umbral de similitud para detectar fallback

    return max_sim >= threshold


def build_sequence(pairs):
    mapping = {}
    starts = set()
    ends = set()
    for a, b in pairs:
        mapping[a] = b
        starts.add(a)
        if b is not None:
            ends.add(b)
    # Find starting words (appear in 'starts' but not in 'ends')
    start_words = starts - ends
    start_words.discard(None)
    sequences = []
    for start_word in start_words:
        sequence = [start_word]
        current_word = start_word
        while current_word in mapping and mapping[current_word] is not None:
            current_word = mapping[current_word]
            sequence.append(current_word)
        sequences.append(sequence)

    if not sequences:
        raise ValueError("Cannot determine a unique starting point.")
    return sequences


def get_random_date():
    year = random.randint(0, 3000)
    month = random.randint(1, 12)

    if month in [1, 3, 5, 7, 8, 10, 12]:
        day = random.randint(1, 31)
    elif month == 2:
        if year % 4 == 0:
            day = random.randint(1, 29)
        else:
            day = random.randint(1, 28)
    else:
        day = random.randint(1, 30)

    return f"{day}/{month}/{year}"


def get_date_range(start, end, step, date_type):

    if 'linspace' in date_type:
        total_seconds = (end - start).total_seconds()
        interval_seconds = total_seconds / (step - 1) if step > 1 else 0
        range_date_list = [(start + timedelta(seconds=interval_seconds * i)).strftime('%d/%m/%Y') for i in range(step)]

    elif date_type in ['day', 'month', 'year']:
        if 'month' in date_type:
            step = 30*step
        elif 'year' in date_type:
            step = 365*step

        range_date_list = [start.strftime('%d/%m/%Y')]
        while end > start:
            start = start + timedelta(days=step)
            range_date_list.append(start.strftime('%d/%m/%Y'))

    elif 'random' in date_type:
        delta = end - start
        random_dates = [
            (start + timedelta(days=random.randint(0, delta.days))).strftime('%d/%m/%Y') for _ in range(step)
        ]
        return random_dates

    else:
        raise InvalidFormat(f"The following parameter does not belong to date range field: {date_type}")

    return range_date_list


def get_date_list(date):
    if isinstance(date, str) and 'random' in date:
        value = int(re.findall(r'random\((.*?)\)', date)[0])
        random_dates = []
        for i in range(value):
            str_date = get_random_date()
            random_dates.append(str_date)
        return random_dates

    elif isinstance(date, dict):
        if 'set' in date:
            value = int(re.findall(r'today\((.*?)\)', date['set'])[0])

            if '>today' in date['set']:
                today = datetime.now()
                next_dates = [
                    (today + timedelta(days=random.randint(1, 365))).strftime('%d/%m/%Y') for _ in range(value)
                ]
                return next_dates

            elif '<today' in date['set']:
                today = datetime.now()
                previous_dates = [
                    (today - timedelta(days=random.randint(1, 365))).strftime('%d/%m/%Y') for _ in range(value)
                ]
                return previous_dates

        elif 'range' in date:
            start = datetime.strptime(date['range']['min'], '%d/%m/%Y')
            end = datetime.strptime(date['range']['max'], '%d/%m/%Y')
            if 'step' in date['range']:
                step_value = int(re.findall(r'\((.*?)\)', date['range']['step'])[0])

                if 'linspace' in date['range']['step']:
                    list_of_dates = get_date_range(start, end, step_value, 'linspace')
                    return list_of_dates

                elif 'day' in date['range']['step']:
                    list_of_dates = get_date_range(start, end, step_value, 'day')
                    return list_of_dates

                elif 'month' in date['range']['step']:
                    list_of_dates = get_date_range(start, end, step_value, 'month')
                    return list_of_dates

                elif 'year' in date['range']['step']:
                    list_of_dates = get_date_range(start, end, step_value, 'year')
                    return list_of_dates
                else:
                    raise InvalidFormat(f"The following parameter does not belong "
                                        f"to date range field: {date['range']['step']}")

            elif 'random' in date['range']:
                value = date['range']['random']
                list_of_dates = get_date_range(start, end, value, 'random')
                return list_of_dates

        # elif 'custom' in date:
        #     pass


def get_any_items(any_list, item_list):
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "List_of_values",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "answer": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["answer"],
                "additionalProperties": False
            }
        }
    }
    output_list = item_list.copy()

    for data in any_list:
        content = re.findall(r'any\((.*?)\)', data)
        message = [{"role": "system",
                    "content": "You are a helpful assistant that creates a list of whatever the user asks."},
                   {"role": "user",
                    "content": f"A list of any of these: {content}. Avoid putting any of these: {output_list}"}]

        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=message,
            response_format=response_format
        )

        raw_data = json.loads(response.choices[0].message.content)
        output_data = raw_data["answer"]

        output_list += output_data

    return output_list
