import random
from resources.utilities import *


class ask_about_class:

    def __init__(self, data):

        self.variable_list = self.get_variables(data)
        self.str_list = self.get_phrases(data)
        self.picked_elements = []
        self.handlers = {'random': self.random_handler}
        self.phrases = self.ask_about_processor(data)

    def get_variables(self, data):
        variables = {}
        for item in data:
            if isinstance(item, dict):
                variables.update(item)
        return variables

    def get_phrases(self, data):
        str_content = []
        for item in data:
            if isinstance(item, str):
                str_content.append(item)
        return str_content

    def random_handler(self, values, count=''):
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
        # Busca todas las variables con formatos manejados
        matches = re.finditer(r'{{(\w+)\.(\w+)(?:\((\w*)\))?}}', text)
        for match in matches:
            var_name = match.group(1)
            handler_name = match.group(2)
            count = match.group(3) if match.group(3) else ''
            if var_name in variables and handler_name in self.handlers:
                replacement = self.handlers[handler_name](self.variable_list[var_name], count)
                self.picked_elements.append({var_name: replacement})
                replacement_srt = ', '.join(replacement)
                text = text.replace(match.group(0), replacement_srt)

        # Reemplaza variables en el formato {{variable}}
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
