import yaml
import os
import json
from datetime import datetime

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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


def set_language(lang_yml):

    if lang_yml is None:
        print("Empty. Setting language to Default (English)")
        language = "English"
        language = f". Please, always talk in {language}. "
        return language
    else:
        print(lang_yml)
        language = lang_yml
        language = f". Please, always talk in {language}. "
        return language


def list_to_phrase(s_list: list, prompted=False):

    #s_list: list of strings
    #l_string: string values extracted from s_list in string format
    l_string = s_list[0]
    if prompted:
        if len(s_list) <= 1:
            return f"If any of this information was provided, you can also ask about {s_list[0]}"

        else:
            for i in range(len(s_list) - 1):
                if s_list[i + 1] == s_list[-1]:
                    l_string = f" {l_string} or {s_list[i + 1]}. "
                else:
                    l_string = f" {l_string}, {s_list[i + 1]} "

            l_string = "If any of this information was provided, you can also ask about" + l_string
            return l_string
    else:
        if len(s_list) <= 1:
            return f"{s_list[0]}"

        else:
            for i in range(len(s_list) - 1):
                if s_list[i + 1] == s_list[-1]:
                    l_string = f" {l_string} or {s_list[i + 1]}"
                else:
                    l_string = f" {l_string}, {s_list[i + 1]}"

            l_string = l_string
            return l_string


def read_yaml(file):
    with open(file, 'r', encoding="UTF-8") as f:
        yam_file = yaml.safe_load(f)
    return yam_file

def save_test_conv(history, metadata, test_name, path):

    print("Saving conversation...")
    data = {**history, **metadata}

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(path, f'{test_name}_{timestamp}.yml')
    with open(file_path, "w", encoding="UTF-8") as archivo:
        yaml.dump(data, archivo, allow_unicode=True, default_flow_style=False)
    print(f"Conversation saved in {path}")



def preprocess_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Eliminar signos de puntuación
    text = re.sub(r'[^\w\s]', '', text)
    return text

def str_to_bool(s):
    return {'true': True, 'false': False}[s.lower()]

def nlp_processor(msg, patterns=None, threshold=0.5):

    # try:
    #
    #     if os.path.isdir(patterns) == True:
    #          read_patterns = read_yaml(patterns_path)
    #     else:
    #          read_patterns = patterns
    # except Exception as e:
    #     print(f"An error occurred: {e}")

    # read_patterns = read_yaml(patterns)
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


# def is_fallback(msg):
#
#     fallaback_patterns = read_yaml("src/testing/user_sim/fallback_patterns.yml")
#
#     # Preprocesar los patrones de fallback
#     fallaback_patterns = [preprocess_text(pattern) for pattern in fallaback_patterns["fallback_patterns"]]
#
#     # Vectorizador TF-IDF
#     vectorizer = TfidfVectorizer().fit(fallaback_patterns)
#
#     processed_msg = preprocess_text(msg)
#
#     # Vectorizar el mensaje y los patrones de fallback
#     vectors = vectorizer.transform([processed_msg] + fallaback_patterns)
#     vector_msg = vectors[0]
#     patt_msg = vectors[1:]
#
#     # Calcular similitud de coseno
#     similarities = cosine_similarity(vector_msg, patt_msg)
#     max_sim = similarities.max()
#
#     # Definir un umbral de similitud para detectar fallback
#     threshold = 0.5
#     return max_sim >= threshold
