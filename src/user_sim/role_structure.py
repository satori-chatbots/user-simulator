from pydantic import BaseModel, ValidationError
import random
import logging
from typing import List, Union
from .interaction_styles import *
from .ask_about import *
from .utils.exceptions import *
from .utils.languages import Languages
from .utils.globals import *

goal_styles = {
    'all answered': '',
    'default': ''
}


def pick_goal_style(goal):
    # try:
    if goal is None:
        return goal, goal_styles['default']
    elif 'steps' in goal:
        if goal['steps'] < 20:
            return list(goal.keys())[0], goal['steps']
        else:
            raise OutOfLimitException(f"Goal steps higher than 20 steps: {goal['random steps']}")
    elif 'all answered' in goal:
        return goal, goal_styles['all answered']
    elif 'random steps' in goal:
        if goal['random steps'] < 20:
            return list(goal.keys())[0], random.randint(1, goal['random steps'])
        else:
            raise OutOfLimitException(f"Goal steps higher than 20 steps: {goal['random steps']}")
    else:
        raise InvalidGoalException(f"Invalid goal value: {goal}")


def replace_placeholders(phrase, variables):
    def replacer(match):
        key = match.group(1)
        if isinstance(variables, dict):
            return ', '.join(map(str, variables.get(key, [])))
        else:
            return ', '.join(map(str, variables))

    pattern = re.compile(r'\{\{(\w+)\}\}')
    return pattern.sub(replacer, phrase)


def set_language(lang):

   if isinstance(lang, type(None)):
        return "English"
   try:
       if lang in Languages:
            return lang
       else:
           raise InvalidLanguageException(f'Invalid language input: {lang}. Setting language to default (English)')
   except InvalidLanguageException as e:
       logging.getLogger().verbose(f'Error: {e}')
       return "English"

def list_to_str(list_of_strings):
    if list_of_strings is None:
        return ''
    try:
        single_string = ' '.join(list_of_strings)
        return single_string
    except Exception as e:
        logging.getLogger().verbose(f'Error: {e}')
        return ''

class RoleDataModel(BaseModel):
    fallback: str
    temperature: float
    isstarter: bool
    role: str
    context: Union[List[str], None]
    ask_about: list
    output: list
    conversations: list
    language: Union[str, None]
    test_name: str

class role_data:

    def __init__(self, path):
        self.yaml = read_yaml(path)

        try:
            self.validated_data = RoleDataModel(**self.yaml)
        except ValidationError as e:
            print(e.json())
            raise

        self.fallback = self.validated_data.fallback
        self.temperature = self.validated_data.temperature
        self.isstarter = self.validated_data.isstarter
        self.role = self.validated_data.role
        self.context = list_to_str(self.validated_data.context) #list
        self.ask_about = ask_about_class(self.validated_data.ask_about) #list
        self.output = self.validated_data.output #dict

        conversation = self.list_to_dict_reformat(self.validated_data.conversations)

        self.conversation_number = conversation['number']
        self.goal_style = pick_goal_style(conversation['goal_style']) #list
        self.language = set_language(self.validated_data.language) #str
        self.interaction_styles = self.pick_interaction_style(conversation['interaction_style']) #list
        self.test_name = self.validated_data.test_name #str

    def reset_attributes(self):
        self.fallback = self.validated_data.fallback
        self.temperature = self.validated_data.temperature
        self.isstarter = self.validated_data.isstarter
        self.role = self.validated_data.role
        self.context = list_to_str(self.validated_data.context) #list
        self.ask_about = ask_about_class(self.validated_data.ask_about)

        conversation = self.list_to_dict_reformat(self.validated_data.conversations)
        self.goal_style = pick_goal_style(conversation['goal_style']) #list
        self.language = set_language(self.validated_data.language) #str
        self.interaction_styles = self.pick_interaction_style(conversation['interaction_style']) #list

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
            'default': default()
        }

        def choice_styles(interaction_styles):
            count = random.randint(1, len(interaction_styles))
            random_list = random.sample(interaction_styles, count)
            # print(f'numero de interaction_style: {count}') #todo: borrar
            logging.getLogger().verbose(f'interaction style amount: {count} style(s): {random_list}')
            return random_list

        def get_styles(interactions):
            interactions_list = []
            try:
                for inter in interactions:

                    if isinstance(inter, dict):
                        keys = list(inter.keys())
                        if keys[0] == "change language":
                            interaction = inter_styles[keys[0]]
                            interaction.languages_options = inter.get(keys[0]).copy()
                            interaction.change_language_flag = True
                            interactions_list.append(interaction)

                    else:
                        if inter in inter_styles:
                            interaction = inter_styles[inter]
                            interactions_list.append(interaction)
                        else:
                            raise InvalidInteractionException(f"Invalid interaction: {inter}")
            except InvalidInteractionException as e:
                print(f"Error: {e}")
                # return None
            return interactions_list

        # interactions_list = []
        if interactions is None:
            interaction = inter_styles['default']
            return [interaction]

        elif isinstance(interactions[0], dict): #todo: add validation funct to admit random only if it alone in the list
            inter_keys = list(interactions[0].keys())

            if 'random' in inter_keys:
                inter = interactions[0]['random']
                choice = choice_styles(inter)
                return get_styles(choice)

        else:
            return get_styles(interactions)


    def get_language(self):

        for instance in self.interaction_styles:
            if instance.change_language_flag:
                prompt = instance.get_prompt()
                return prompt

        return f"Please, talk in {self.language}"