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

    def __init__(self, default_language):

        self.change_language = False
        self.languages = []

    def get_prompt(self):
        return



class long_phrases(interaction_style):
    def get_prompt(self):
        return "use very long phrases to write anything. "

class change_your_mind(interaction_style):
    def get_prompt(self):
        return "eventually, change your mind about any information you provided. "

class change_language(interaction_style): #TODO: add chance variable with *args


    def get_prompt(self):

        lang = self.get_language()
        return f"Please, always talk in {lang}, even If the assistant tells you that he doesn't understand. "

    def language(self, default_language, chance=50):

        rand_number = random.randint(1, 100)
        if rand_number <= chance:
            lang = random.choice(self.languages)
            print(f'the language is: {lang}')
            self.languages.append(lang)
            return lang
        else:
            self.languages.append(default_language)
            print(f'the language was set to default')
            return f"Please, talk in {default_language}"


class make_spelling_mistakes(interaction_style):
    def get_prompt(self):
        prompt = """
                 please, make several spelling mistakes or typos in the sentences you're generating. 
                 But I mean, a lot, like, minimum 5 typos per sentence if possible. 
                 """
        return prompt

class single_questions(interaction_style):
    def get_prompt(self):
        return "ask only one question per interaction. "

class all_questions(interaction_style):
    def get_prompt(self):
        return "ask everything you have to ask in one sentence. "

class default(interaction_style):
    def get_prompt(self):
        return ''