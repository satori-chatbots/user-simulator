import yaml
import os
import json
import configparser
from datetime import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import importlib.util
from .exceptions import *

logger = logging.getLogger('my_app_logger')


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


def list_to_phrase(s_list: list, prompted=False):  #todo: cambiar a list_to_askabout
    #s_list: list of strings
    #l_string: string values extracted from s_list in string format
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
    serial = datetime.now().strftime("%Y%m%d%H%M%S") + f"{now.microsecond // 1000:03d}"
    return serial


class MyDumper(yaml.Dumper):
    def write_line_break(self, data=None):
        super().write_line_break(data)
        super().write_line_break(data)


def save_test_conv(history, metadata, test_name, path, serial, conversation_time, av_data, counter):
    print("Saving conversation...")
    c_time = {'conversation time': conversation_time}
    path_folder = path + f"/{test_name}"
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    data = [metadata, c_time, history]
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


def check_keys(key_list: list):
    if os.path.exists("keys.properties"):
        #logging.getLogger().verbose("properties found!")
        logging.info("properties found!")
        config = configparser.ConfigParser()
        config.read('keys.properties')

        # Loop over all keys and values
        for key in config['keys']:
            key = key.upper()
            os.environ[key] = config['keys'][key]

    for k in key_list:
        if not os.environ.get(k):
            raise Exception(f"{k} not found")


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
