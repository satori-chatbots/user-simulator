import random
import copy
from .utils.exceptions import *
from .utils.utilities import *
import numpy as np


# class VarGenerators:
#
#     def __init__(self, value_list, funct):
#
#
#         self.value_list = value_list
#         self.funct = funct
#         self.dependence_variable = None
#         self.flag = True
#         self.last_return = None
#         self.generator = self.create_generator()
#
#     def get_gen(self):
#         item = next(self.generator)
#         self.last_return = item.copy()
#         return item
#
#     def create_generator(self):
#         pattern = r'(\w+)\((\w*)\)'
#         match = re.search(pattern, self.funct)
#         if match:
#             handler_name = match.group(1)
#             count = match.group(2) if match.group(2) else ''
#             if handler_name == 'random':
#                 if count == '':
#                     generator = self.random_choice_generator()
#                     return generator
#                 elif count.isdigit():
#                     generator = self.random_choice_count_generator(count)
#                     return generator
#                 elif count == 'rand':
#                     generator = self.random_choice_random_count_generator()
#                     return generator
#
#             elif handler_name == 'forward':
#                 if count != '':
#                     self.dependence_variable = count
#                 generator = self.forward_generator()
#                 return generator
#
#             elif handler_name == 'another':
#                 generator = self.another_generator()
#                 return generator
#
#             else:
#                 raise InvalidGenerator(f'Invalid generator function: {handler_name}')
#         else:
#             raise InvalidFormat(f"an invalid function format was used: {self.funct}")
#
#     def random_choice_generator(self):
#         while True:
#             yield [random.choice(self.value_list)]
#
#     def random_choice_count_generator(self, count):
#         while True:
#             sample = random.sample(self.value_list, min(count, len(self.value_list)))
#             yield sample
#
#     def random_choice_random_count_generator(self):
#         while True:
#             count = random.randint(1, len(self.value_list))
#             sample = random.sample(self.value_list, min(count, len(self.value_list)))
#             yield sample
#
#     def forward_generator(self):
#         while True:
#             for sample in self.value_list:
#                 self.flag = True if sample == self.value_list[-1] else False
#                 yield [sample]
#
#
#     def another_generator(self):
#         while True:
#             copy_list = self.value_list[:]
#             random.shuffle(copy_list)
#             for sample in copy_list:
#                 yield sample

# def build_sequence(pairs):
#     mapping = {}
#     starts = set()
#     ends = set()
#     for a, b in pairs:
#         mapping[a] = b
#         starts.add(a)
#         ends.add(b)
#     # Find the starting word (appears in 'starts' but not in 'ends')
#     start = starts - ends
#     if len(start) != 1:
#         raise ValueError("Cannot determine a unique starting point.")
#     current_word = start.pop()
#     sequence = [current_word]
#     while current_word in mapping:
#         current_word = mapping[current_word]
#         sequence.append(current_word)
#     return sequence



class VarGenerators:

    def __init__(self, variable_list):

        self.variable_list = variable_list
        self.generator_list = self.create_generator_list()

    class ForwardMatrixGenerator:
        def __init__(self):
            self.forward_function_list = []
            self.dependence_tuple_list = []  # [(size, toppings), (toppings,drink), (drink, None)]
            self.dependent_list = []
            self.independent_list = []
            self.dependence_matrix = []
            self.dependent_generators = []
            self.independent_generators = []

        def get_matrix(self, dependent_variable_list):
            self.dependence_matrix.clear()
            for index, dependence in enumerate(dependent_variable_list):
                self.dependence_matrix.append([])
                for variable in dependence:
                    for forward in self.forward_function_list:
                        if variable == forward['name']:
                            self.dependence_matrix[index].append(forward['data'])

        def add_forward(self, forward_variable): # 'name': var_name, 'data': data_list,'function': content['function'],'dependence': dependence}
            self.forward_function_list.append(forward_variable)

            if forward_variable['dependence']:
                master = forward_variable['dependence']
                slave = forward_variable['name']
                self.dependence_tuple_list.append((slave, master))
                for indep_item in self.independent_list:
                    if indep_item == master:
                        self.independent_list.remove(master)
                        self.dependence_tuple_list.append((master, None))

            else:
                if self.dependence_tuple_list:
                    dtlc = self.dependence_tuple_list.copy()
                    for dependence in dtlc:  # [(size, toppings), (toppings,drink), (drink, None)]
                        if forward_variable['name'] in dependence:
                            master = forward_variable['name']
                            self.dependence_tuple_list.append((master, None))
                            break
                    else:
                        master = forward_variable['name']
                        self.independent_list.append(master)
                else:
                    master = forward_variable['name']
                    self.independent_list.append(master)

            if self.dependence_tuple_list:
                self.dependent_list = build_sequence(self.dependence_tuple_list)
                self.get_matrix(self.dependent_list)

        @staticmethod
        def combination_generator(matrix):
            if not matrix:
                while True:
                    yield []
            else:
                lengths = [len(lst) for lst in matrix]
                indices = [0] * len(matrix)
                while True:
                    # Yield the current combination based on indices
                    yield [matrix[i][indices[i]] for i in range(len(matrix))]
                    # Increment indices from the last position
                    i = len(matrix) - 1
                    while i >= 0:
                        indices[i] += 1
                        if indices[i] < lengths[i]:
                            break
                        else:
                            indices[i] = 0
                            i -= 1

        @staticmethod
        def forward_generator(value_list):
            while True:
                for sample in value_list:
                    yield [sample]

        def get_generator_list(self):

            function_map = {function['name']: function['data'] for function in self.forward_function_list}
            independent_generators = [
                {'name': i, 'generator': self.forward_generator(function_map[i])} for i in self.independent_list if i in function_map
            ]

            dependent_generators = [
                {'name': val, 'generator': self.combination_generator(self.dependence_matrix[index])} for index, val in enumerate(self.dependent_list)
            ]
            # dependent_generators = {
            #     'name': self.dependent_list, 'generator': self.combination_generator(self.dependence_matrix)
            # }

            return independent_generators + dependent_generators

    def create_generator_list(self):
        generator_list = []
        my_forward = self.ForwardMatrixGenerator()
        for variable in self.variable_list:
            name = variable['name']
            data = variable['data']
            pattern = r'(\w+)\((\w*)\)'
            if not variable['function'] or variable['function'] == 'default()':
                generator = self.default_generator(data)
                generator_list.append({'name': name, 'generator': generator})
            else:
                match = re.search(pattern, variable['function'])
                if match:
                    handler_name = match.group(1)
                    count = match.group(2) if match.group(2) else ''
                    if handler_name == 'random':
                        if count == '':
                            generator = self.random_choice_generator(data)
                            generator_list.append({'name': name, 'generator': generator})
                        elif count.isdigit():
                            count_digit = int(count)
                            generator = self.random_choice_count_generator(data, count_digit)
                            generator_list.append({'name': name, 'generator': generator})
                        elif count == 'rand':
                            generator = self.random_choice_random_count_generator(data)
                            generator_list.append({'name': name, 'generator': generator})

                    elif handler_name == 'forward':
                        my_forward.add_forward(variable)

                    elif handler_name == 'another':
                        generator = self.another_generator(data)
                        generator_list.append({'name': name, 'generator': generator})
                    else:
                        raise InvalidGenerator(f'Invalid generator function: {handler_name}')
                else:
                    raise InvalidFormat(f"an invalid function format was used: {variable['function']}")


        return generator_list + my_forward.get_generator_list()

    @staticmethod
    def default_generator(data):
        while True:
            yield data

    @staticmethod
    def random_choice_generator(data):
        while True:
            yield [random.choice(data)]

    @staticmethod
    def random_choice_count_generator(data, count):
        while True:
            sample = random.sample(data, min(count, len(data)))
            yield sample

    @staticmethod
    def random_choice_random_count_generator(data):
        while True:
            count = random.randint(1, len(data))
            sample = random.sample(data, min(count, len(data)))
            yield sample

    @staticmethod
    def another_generator(data):
        while True:
            copy_list = data[:]
            random.shuffle(copy_list)
            for sample in copy_list:
                yield sample


def reorder_variables(entries):
    def parse_entry(entry):

        match = re.search(r'forward\((.*?)\)', entry['function'])
        if match:
            slave = entry['name']
            master = match.group(1)
            return slave, master

    def reorder_list(dependencies):
        tuple_list = []
        none_list = []
        for main_tuple in dependencies:
            if main_tuple:
                for comp_tuple in dependencies:
                    if comp_tuple:
                        if main_tuple[1] == comp_tuple[0]:
                            tuple_list.append(main_tuple)
                            tuple_list.append(comp_tuple)
            else:
                none_list.append(main_tuple)

        tuple_list = list(dict.fromkeys(tuple_list))
        return tuple_list

    dependencies_list = []

    for entry in entries:
        dependencies_list.append(parse_entry(entry))

    reordered_list = reorder_list(dependencies_list)

    editable_entries = entries.copy()
    new_entries = []
    for tupl in reordered_list:
        for entry in entries:
            if tupl[0] == entry['name']:
                new_entries.append(entry)
                editable_entries.remove(entry)
    reordered_entries = new_entries + editable_entries
    return reordered_entries


def dependency_error_check(variable_list):
    for slave in variable_list:
        for master in variable_list:
            if slave['dependence'] == master['name']:
                pattern = r'(\w+)\((\w*)\)'
                match = re.search(pattern, master['function'])
                function = match.group(1)
                if function != 'forward':
                    raise InvalidDependence(f"the following function doesn't admit dependence: {function}()")

def check_circular_dependency(items):
    # Construir un mapeo de nombre a dependencia
    dependencies = {}
    for item in items:
        name = item['name']
        dep = item['dependence']
        dependencies[name] = dep

    # Función para realizar DFS y detectar ciclos
    def visit(node, visited, stack):
        if node in stack:
            # Se detectó una dependencia circular
            cycle = ' -> '.join(stack + [node])
            raise Exception(f"Circular dependency detected: {cycle}")
        if node in visited or node not in dependencies:
            return
        stack.append(node)
        dep = dependencies[node]
        if dep is not None:
            visit(dep, visited, stack)
        stack.pop()
        visited.add(node)

    visited = set()
    for node in dependencies.keys():
        if node not in visited:
            visit(node, visited, [])

class AskAboutClass:

    def __init__(self, data):

        self.variable_list = self.get_variables(data)
        self.str_list = self.get_phrases(data)
        self.var_generators = self.variable_generator(self.variable_list)
        self.phrases = self.str_list.copy()
        self.picked_elements = []

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

                pattern = r'(\w+)\((\w*)\)'
                if not content['function']:
                    content['function'] = 'default()'

                match = re.search(pattern, content['function'])
                if match:
                    count = match.group(2) if match.group(2) else ''
                    if not count == '' or count == 'rand' or count.isdigit():
                        dependence = count
                    else:
                        dependence = None
                else:
                    dependence = None

                dictionary = {'name': var_name, 'data': data_list,
                              'function': content['function'],
                              'dependence': dependence}  # (size, [small, medium], random(), toppings)
                variables.append(dictionary)
        reordered_variables = reorder_variables(variables)
        dependency_error_check(reordered_variables)
        check_circular_dependency(reordered_variables)
        return reordered_variables

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

    @staticmethod
    def variable_generator(variables):
        generators = VarGenerators(variables)
        generators_list = generators.generator_list
        return generators_list

    def replace_variables(self, generator):
        pattern = re.compile(r'\{\{(.*?)\}\}')
        if isinstance(generator['name'], list) and len(generator['name']) > 1:  # this is for nested forwards

            values = next(generator['generator'])
            keys = generator['name']
            mapped_combinations = dict(zip(keys, values))
            self.picked_elements.extend([{key: value} for key, value in mapped_combinations.items()])
            replaced_phrases = []
            for phrase in self.phrases.copy():
                def replace_variable(match):
                    variable = match.group(1)
                    return mapped_combinations.get(variable, match.group(0))
                replaced_phrase = re.sub(r'\{\{(\w+)\}\}', replace_variable, phrase)
                replaced_phrases.append(replaced_phrase)
            self.phrases = replaced_phrases

        else:                                                   # this is for everything else
            value = next(generator['generator'])
            name = generator['name']

            for index, text in enumerate(self.phrases):
                matches = re.finditer(pattern, text)
                for match in matches:
                    if match.group(1) == name:
                        self.picked_elements.append({match.group(1): value})
                        replacement = ', '.join(value)
                        text = text.replace(match.group(0), replacement)
                        self.phrases[index] = text
                        break
                else:
                    self.phrases[index] = text

    def ask_about_processor(self):
        for generator in self.var_generators:
            self.replace_variables(generator)
        return self.phrases

    def prompt(self):
        phrases = self.ask_about_processor()
        return list_to_phrase(phrases, True)

    def reset(self):
        self.picked_elements = []
        self.phrases = self.str_list.copy()
