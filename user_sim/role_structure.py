import yaml
import re
from user_sim.utilities import *
import random

interaction_styles = {
    'long phrases': "use very long phrases to write anything. ",
    'change your mind': "eventually, change your mind about any information you provided. ",
    'change language': "eventually, change language to any of these: {{langauge}}. ",
    'make spelling mistakes': "please, make several spelling mistakes or typos in the sentences you're generating. "
                              "But I mean, a lot, like, minimum 5 typos per sentence if possible. ",
    'single question': "ask only one question per interaction. ",
    'all questions': "ask everything you have to ask in one sentence. ",
    'default': ''
}

goal_styles = {
    'all answered': '',
    'default': ''
}


def pick_goal_style(goal):

    if goal is None:
        return goal, goal_styles['default']

    else:
        if 'steps' in goal:
            return list(goal.keys())[0], goal['steps']
        else:
            return goal, goal_styles['all answered']

def replace_placeholders(phrase, variables):
    def replacer(match):
        key = match.group(1)
        if isinstance(variables, dict):
            return ', '.join(map(str, variables.get(key, [])))
        else:
            return ', '.join(map(str, variables))

    pattern = re.compile(r'\{\{(\w+)\}\}')
    return pattern.sub(replacer, phrase)

class interaction_style:

    def __init__(self, interaction_dict):

        self.interactions = []
        self.interactions_prompt = list_to_str(self.interactions)
        self.change_language = False
        self.languages = []

        self.pick_interaction_style(interaction_dict)

    def pick_interaction_style(self, interactions):

        if interactions is None:
            return self.interactions.append(interaction_styles['default'])

        for inter in interactions:

            if isinstance(inter, dict):
                keys = list(inter.keys())
                if keys[0] == "change language":
                    self.languages = inter.get(keys[0])
                    self.change_language = True

            else:
                self.interactions.append(interaction_styles[inter])


def set_language(lang): #TODO: try add a specific language and affect it with the "change language" interaction style
    if isinstance(lang, type(None)):
        return ''
    else:
        return f"Please, talk in {lang}"

def list_to_str(list_of_strings):
    single_string = ' '.join(list_of_strings)
    return single_string


class role_data:

    def __init__(self, path):

        self.yaml = read_yaml(path)
        self.fallback = self.yaml['fallback']
        self.temperature = self.yaml["temperature"]
        self.isstarter = self.yaml["isstarter"]
        self.role = self.yaml["role"]
        self.context = list_to_str(self.yaml["context"])
        self.ask_about = self.ask_about_processor(self.yaml["ask_about"])
        self.conversation_number = self.list_to_dict_reformat(self.yaml["conversations"])['number']
        self.goal_style = pick_goal_style(self.list_to_dict_reformat(self.yaml["conversations"])['goal_style'])
        self.interaction_styles = interaction_style(self.list_to_dict_reformat(self.yaml["conversations"])['interaction_style'])
        self.language = set_language(self.yaml["language"])
        self.test_name = self.yaml["test_name"]

    def list_to_dict_reformat(self, conv):
        result_dict = {k: v for d in conv for k, v in d.items()}
        return result_dict

    def get_language(self, chance=50):

        if self.interaction_styles.change_language:
            rand_number = random.randint(1, 100)
            if rand_number <= chance:
                lang = random.choice(self.interaction_styles.languages)
                print(f'the language is: {lang}')
                return f"Please, always talk in {lang}, even If the assistant tells you that he doesn't understand. "
            else:
                return f"Please, talk in {self.language}"
        else:
            return f"Please, talk in {self.language}"


    def ask_about_processor(self, data):

        variables = {}
        for item in data:
            if isinstance(item, dict):
                variables.update(item)
                print(variables)

        result_phrases = []
        for item in data:
            if isinstance(item, str):

                if re.search(r'\{\{\w+\}\}', item):
                    updated_phrase = replace_placeholders(item, variables)
                    result_phrases.append(updated_phrase)
                else:
                    result_phrases.append(item)

        return result_phrases
