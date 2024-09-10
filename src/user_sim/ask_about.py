import random
from .utils.exceptions import *
from .utils.utilities import *
import numpy as np


class VarGenerators:

    def __init__(self, value_list, funct):

        self.value_list = value_list
        self.funct = funct
        self.generator = self.create_generator()
        self.dependence_variable = None
        self.first_execution = True
        self.flag = True
        self.last_return = None



    def get_gen(self):
        item = next(self.generator)
        self.first_execution = False
        self.last_return = item.copy()
        return item

    def create_generator(self):
        pattern = r'(\w+)\((\w*)\)'
        match = re.search(pattern, self.funct)
        if match:
            handler_name = match.group(1)
            count = match.group(2) if match.group(2) else ''
            if handler_name == 'random':
                if count == '':
                    generator = self.random_choice_generator()
                    return generator
                elif count.isdigit():
                    generator = self.random_choice_count_generator(count)
                    return generator
                elif count == 'rand':
                    generator = self.random_choice_random_count_generator()
                    return generator

            elif handler_name == 'forward':
                if count != '':
                    self.dependence_variable = count
                generator = self.forward_generator()
                return generator

            # elif handler_name == 'forward_dependence':
            #     generator = self.forward_dependence_generator()
            #     return generator

            elif handler_name == 'another':
                generator = self.another_generator()
                return generator

            else:
                raise InvalidGenerator(f'Invalid generator function: {handler_name}')
        else:
            raise InvalidFormat(f"an invalid function format was used: {self.funct}")

    def random_choice_generator(self):
        while True:
            yield [random.choice(self.value_list)]

    def random_choice_count_generator(self, count):
        while True:
            sample = random.sample(self.value_list, min(count, len(self.value_list)))
            yield sample

    def random_choice_random_count_generator(self):
        while True:
            count = random.randint(1, len(self.value_list))
            sample = random.sample(self.value_list, min(count, len(self.value_list)))
            yield sample

    def forward_generator(self):
        while True:
            for sample in self.value_list:
                self.flag = False
                yield [sample]
            self.flag = True


    def another_generator(self):
        while True:
            copy_list = self.value_list[:]
            random.shuffle(copy_list)
            for sample in copy_list:
                yield sample


class AskAboutClass:

    def __init__(self, data):

        self.variable_list = self.get_variables(data)
        self.str_list = self.get_phrases(data)
        self.picked_elements = []
        self.var_generators = self.variable_generator(self.variable_list)
        self.phrases = []

    @staticmethod
    def get_variables(data):
        variables = []

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
                            raise MissingStepDefinition(
                                f'"step" or "lisnpace" parameter missing. A step separation must be defined.')
                    else:
                        raise InvalidFormat(f'Data follows an invalid format.')
                else:
                    raise InvalidItemType(f'Invalid data type for variable list.')

                dictionary = {'name': var_name, 'data': data_list, 'function': content['function']} #(size, [small, medium], random())
                variables.append(dictionary)
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

    def variable_generator(self, variables):

        generators = []
        for var in variables:
            generator = VarGenerators(var['data'], var['function'])
            generators.append({'name': var['name'], 'generator': generator})

        return generators

    def analyze_dependency(self, generator, var_generators):

        if 'depend' in generator.func:
            pass

        else:
            return generator.get_gen()


    def replace_variables(self, text):

        matches = re.finditer(r'{{(\w+)}}', text)
        for match in matches:
            for gen in self.var_generators:
                if match.group(1) == gen['name']:
                    generator = gen['generator']
                    value = generator.get_gen()
                    self.picked_elements.append({match.group(1): value})
                    replacement = ', '.join(value)
                    text = text.replace(match.group(0), replacement)
        return text


    def ask_about_processor(self, phrases):
        result_phrases = []
        for text in phrases:
            result_phrases.append(self.replace_variables(text))

        return result_phrases

    def prompt(self):
        phrases = self.ask_about_processor(self.str_list)
        self.phrases = phrases
        return list_to_phrase(phrases, True)

    def reset(self):
        self.picked_elements = []
        self.phrases = []