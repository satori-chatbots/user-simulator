import yaml
import re
from user_sim.utilities import *
import random
from interaction_styles import *
from ask_about import *


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

# class interaction_style:
#
#     def __init__(self, interaction_dict):
#
#         self.interactions = []
#         self.interactions_prompt = list_to_str(self.interactions)
#         self.change_language = False
#         self.languages = []
#
#         self.pick_interaction_style(interaction_dict)




def set_language(lang): #TODO: try add a specific language and affect it with the "change language" interaction style
    if isinstance(lang, type(None)):
        return "English"
    else:
        return lang

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
        # self.ask_about = self.ask_about_processor(self.yaml["ask_about"])
        self.ask_about = ask_about_class(self.yaml["ask_about"])
        self.conversation_number = self.list_to_dict_reformat(self.yaml["conversations"])['number']
        self.goal_style = pick_goal_style(self.list_to_dict_reformat(self.yaml["conversations"])['goal_style'])
        self.language = set_language(self.yaml["language"])
        self.interaction_styles = self.pick_interaction_style(self.list_to_dict_reformat(self.yaml["conversations"])['interaction_style'])
        self.test_name = self.yaml["test_name"]

    def list_to_dict_reformat(self, conv):
        result_dict = {k: v for d in conv for k, v in d.items()}
        return result_dict

    def get_interaction_metadata(self):
        metadata_list = []
        for inter in self.interaction_styles:

            metadata_list.append(inter.get_metadata())

        return metadata_list


    def pick_interaction_style(self, interactions):

        inter_styles = {
            'long phrases': long_phrases(),
            'change your mind': change_your_mind(),
            'change language': change_language(self.language),
            'make spelling mistakes': make_spelling_mistakes(),
            'single question': single_questions(),
            'all questions': all_questions(),
            'default': default
        }

        interactions_list = []
        if interactions is None:
            interaction = inter_styles['default']
            return interactions_list.append(interaction)

        for inter in interactions:

            if isinstance(inter, dict):
                keys = list(inter.keys())
                if keys[0] == "change language":
                    interaction = inter_styles[keys[0]]
                    interaction.languages_options = inter.get(keys[0]).copy()
                    interaction.change_language_flag = True
                    interactions_list.append(interaction)

            else:
                interaction = inter_styles[inter]
                interactions_list.append(interaction)
        return interactions_list



    def get_language(self):

        for instance in self.interaction_styles:
            if instance.change_language_flag:
                prompt = instance.get_prompt()
                return prompt

        return f"Please, talk in {self.language}"




    # class ask_about_class:
    #
    #     def __init__(self, data):
    #
    #         self.variable_list = self.get_variables(data)
    #         self.str_list = self.get_phrases(data)
    #         self.picked_elements = []
    #         self.handlers = {'random': self.random_handler}
    #         self.phrases = self.ask_about_processor(data)
    #
    #     def get_variables(self, data):
    #         variables = {}
    #         for item in data:
    #             if isinstance(item, dict):
    #                 variables.update(item)
    #         return variables
    #
    #     def get_phrases(self, data):
    #         str_content = []
    #         for item in data:
    #             if isinstance(item, str):
    #                 str_content.append(item)
    #         return str_content
    #
    #     def random_handler(self, values, count=''):
    #         if count == '':
    #             return [random.choice(values)]
    #         elif count.isdigit():
    #             count = int(count)
    #             return random.sample(values, min(count, len(values)))
    #         elif count == 'rand':
    #             count = random.randint(1, len(values))
    #             return random.sample(values, count)
    #         return values #TODO: exception for .random(xxx) invalid parameter
    #
    #
    #     def replace_variables(self, text, variables):
    #         # Busca todas las variables con formatos manejados
    #         matches = re.finditer(r'{{(\w+)\.(\w+)(?:\((\w*)\))?}}', text)
    #         for match in matches:
    #             var_name = match.group(1)
    #             handler_name = match.group(2)
    #             count = match.group(3) if match.group(3) else ''
    #             if var_name in variables and handler_name in self.handlers:
    #                 replacement = self.handlers[handler_name](self.variable_list[var_name], count)
    #                 self.picked_elements.append({var_name: replacement})
    #                 replacement_srt = ', '.join(replacement)
    #                 text = text.replace(match.group(0), replacement_srt)
    #
    #         # Reemplaza variables en el formato {{variable}}
    #         matches = re.finditer(r'{{(\w+)}}', text)
    #         for match in matches:
    #             var_name = match.group(1)
    #             if var_name in variables:
    #                 self.picked_elements.append(variables)
    #                 replacement = ', '.join(variables[var_name])
    #                 text = text.replace(match.group(0), replacement)
    #
    #         return text
    #
    #     def ask_about_processor(self, data):
    #
    #         result_phrases = []
    #         for item in data:
    #             if isinstance(item, str):
    #                 result_phrases.append(self.replace_variables(item, self.variable_list))
    #
    #         return result_phrases
    #
    #     def prompt(self):
    #         return list_to_phrase(self.phrases, True)

    # def ask_about_processor(self, data):
    #
    #     variables = {}
    #     for item in data:
    #         if isinstance(item, dict):
    #
    #             variables.update(item)
    #             print(variables)
    #
    #     result_phrases = []
    #     for item in data:
    #         if isinstance(item, str):
    #
    #             if re.search(r'\{\{\w+\}\}', item):
    #                 updated_phrase = replace_placeholders(item, variables)
    #                 result_phrases.append(updated_phrase)
    #             else:
    #                 result_phrases.append(item)
    #
    #     return result_phrases