import random
from .utils.utilities import *


class AskAboutClass:

    def __init__(self, data):

        self.variable_list = self.get_variables(data)
        self.str_list = self.get_phrases(data)
        self.picked_elements = []
        self.handlers = {'random': self.random_handler}
        self.phrases = self.ask_about_processor(data)

    @staticmethod
    def get_variables(data):
        variables = {}
        for item in data:
            if isinstance(item, dict):
                variables.update(item)
        return variables

    @staticmethod
    def get_phrases(data):
        str_content = []
        for item in data:
            if isinstance(item, str):
                str_content.append(item)
        return str_content

    @staticmethod
    def random_handler(values, count=''):
        if count == '':
            return [random.choice(values)]
        elif count.isdigit():
            count = int(count)
            return random.sample(values, min(count, len(values)))
        elif count == 'rand':
            count = random.randint(1, len(values))
            return random.sample(values, count)
        return values  # TODO: exception for .random(xxx) invalid parameter

    def replace_variables(self, text, variables):
        matches = re.finditer(r'{{(\w+)\.(\w+)(?:\((\w*)\))?}}', text)
        for match in matches:
            var_name = match.group(1)
            handler_name = match.group(2)
            count = match.group(3) if match.group(3) else ''
            if var_name in variables and handler_name in self.handlers:
                replacement = self.handlers[handler_name](self.variable_list[var_name], count)
                self.picked_elements.append({var_name: replacement})
                replacement_srt = ', '.join(map(str, replacement))
                text = text.replace(match.group(0), replacement_srt)

        matches = re.finditer(r'{{(\w+)}}', text)
        for match in matches:
            var_name = match.group(1)
            if var_name in variables:
                self.picked_elements.append(variables)
                replacement = ', '.join(variables[var_name])
                text = text.replace(match.group(0), replacement)

        return text

    def ask_about_processor(self, data):

        result_phrases = []
        for item in data:
            if isinstance(item, str):
                result_phrases.append(self.replace_variables(item, self.variable_list))

        return result_phrases

    def prompt(self):
        return list_to_phrase(self.phrases, True)
