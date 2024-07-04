import pydantic
import random

# interaction_styles = {
#     'long phrases': "use very long phrases to write anything. ",
#     'change your mind': "eventually, change your mind about any information you provided. ",
#     'change language': "eventually, change language to any of these: {{langauge}}. ",
#     'make spelling mistakes': "please, make several spelling mistakes or typos in the sentences you're generating. "
#                               "But I mean, a lot, like, minimum 5 typos per sentence if possible. ",
#     'single question': "ask only one question per interaction. ",
#     'all questions': "ask everything you have to ask in one sentence. ",
#     'default': ''
# }


def find_instance(instances, iclass):
    for instance in instances:
        if isinstance(instance, iclass):
            return instance
    return None

def create_instance(class_list, interaction_syles):
    instances = []
    for class_info in class_list:
        class_name = class_info['clase']
        args = class_info.get('args', [])
        kwargs = class_info.get('kwargs', {})
        if class_name in interaction_syles:
            instance = interaction_syles[class_name](*args, **kwargs)
            instances.append(instance)
        else:
            raise ValueError(f"Couldn't find {class_name} in interaction list.")
    return instances

class interaction_style:

    def __init__(self, intertype):
        self.intertype = intertype
        self.change_language_flag = False
        self.languages_options = []

    def get_prompt(self):
        return

    def get_metadata(self):
        return


class long_phrases(interaction_style):
    def __init__(self):
        super().__init__(intertype='long phrases')
    def get_prompt(self):
        return "use very long phrases to write anything. "
    def get_metadata(self):
        return self.intertype

class change_your_mind(interaction_style):
    def __init__(self):
        super().__init__(intertype='change your mind')
    def get_prompt(self):
        return "eventually, change your mind about any information you provided. "
    def get_metadata(self):
        return self.intertype

class change_language(interaction_style): #TODO: add chance variable with *args
    def __init__(self, default_language):
        super().__init__(intertype='change language')
        self.default_language = default_language
        self.languages_list = []

    def get_prompt(self):

        lang = self.language()
        return f"Please, always talk in {lang}, even If the assistant tells you that he doesn't understand. "

    def language(self, chance=50):

        rand_number = random.randint(1, 100)
        if rand_number <= chance:
            lang = random.choice(self.languages_options)
            print(f'the language is: {lang}')
            self.languages_list.append(lang)
            return lang
        else:
            self.languages_list.append(self.default_language)
            print(f'the language was set to default')
            return self.default_language

    def get_metadata(self):
        return {'change languages': self.languages_list}


class make_spelling_mistakes(interaction_style):
    def __init__(self):
        super().__init__(intertype='make spelling mistakes')

    def get_prompt(self):
        prompt = """
                 please, make several spelling mistakes or typos in the sentences you're generating. 
                 But I mean, a lot, like, minimum 5 typos per sentence if possible. 
                 """
        return prompt

    def get_metadata(self):
        return self.intertype

class single_questions(interaction_style):
    def __init__(self):
        super().__init__(intertype='single questions')

    def get_prompt(self):
        return "ask only one question per interaction. "

    def get_metadata(self):
        return self.intertype

class all_questions(interaction_style):
    def __init__(self):
        super().__init__(intertype='all questions')

    def get_prompt(self):
        return "ask everything you have to ask in one sentence. "

    def get_metadata(self):
        return self.intertype

class default(interaction_style):
    def __init__(self):
        super().__init__(intertype='default')

    def get_prompt(self):
        return ''

    def get_metadata(self):
        return self.intertype
