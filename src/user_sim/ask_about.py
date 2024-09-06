import random
from .utils.exceptions import *
from .utils.utilities import *
import numpy as np


class AskAboutClass:

    def __init__(self, data):

        self.variable_list = self.get_variables(data)
        self.str_list = self.get_phrases(data)
        self.picked_elements = []
        self.handlers = {'random': self.random_handler}
        self.phrases = self.ask_about_processor(data)

    @staticmethod
    # def get_variables(data):
    #     variables = {}
    #     for item in data:
    #         if isinstance(item, dict):
    #             variables.update(item)
    #     return variables
    def get_variables(data):
        variables = {}

        for item in data:
            if isinstance(item, dict):
                var_name = list(item.keys())[0]
                content = item[var_name]
                if content['type'] == 'string':
                    for i in content['data']:
                        if type(i) is not str:
                            raise InvalidDataType(f'The following item is not a string: {i}')

                    if content['data']:
                        data_list = content['data']
                    else:
                        raise EmptyListExcept(f'Data list is empty.')

                elif content['type'] == 'int':
                    if isinstance(content['data'], list):
                        for i in content['data']:
                            if type(i) is not int:
                                raise InvalidDataType(f'The following item is not an integer: {i}')
                        if content['data']:
                            data_list = content['data']
                        else:
                            raise EmptyListExcept(f'Data list is empty.')
                    elif isinstance(content['data'], dict):
                        keys = list(content['data'].keys())
                        data = content['data']
                        if 'step' in keys:
                            if isinstance(data['min'], int) and isinstance(data['max'], int) and isinstance(
                                    data['step'], int):
                                data_list = np.arange(data['min'], data['max'], data['step'])
                            else:
                                raise InvalidDataType(f'Some of the range function parameters are not integers.')
                        else:
                            if isinstance(data['min'], int) and isinstance(data['max'], int):
                                data_list = np.arange(data['min'], data['max'])
                            else:
                                raise InvalidDataType(f'Some of the range function parameters are not integers.')
                    else:
                        raise InvalidFormat(f'Data follows an invalid format.')

                elif content['type'] == 'float':
                    if isinstance(content['data'], list):
                        for i in content['data']:
                            if not isinstance(i, (int, float)):
                                raise InvalidDataType(f'The following item is not a number: {i}')
                        if content['data']:
                            data_list = content['data']
                        else:
                            raise EmptyListExcept(f'Data list is empty.')
                    elif isinstance(content['data'], dict):
                        keys = list(content['data'].keys())
                        data = content['data']
                        if 'step' in keys:
                            data_list = np.arange(data['min'], data['max'], data['step'])
                        elif 'linspace' in keys:
                            data_list = np.linspace(data['min'], data['max'], data['linspace'])
                        else:
                            raise MissingStepDefinition(f'"step" or "lisnpace" parameter missing. A step separation must be defined.')
                    else:
                        raise InvalidFormat(f'Data follows an invalid format.')
                else:
                    raise InvalidItemType(f'Invalid data type for variable list.')

                dictionary = {var_name: data_list}
                variables.update(dictionary)
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
