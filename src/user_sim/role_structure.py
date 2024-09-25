from pydantic import BaseModel, ValidationError
from typing import List, Union, Dict
from .interaction_styles import *
from .ask_about import *
from .utils.exceptions import *
from .utils.languages import Languages
from pathlib import Path

goal_styles = {
    'all answered': '',
    'default': ''
}


def pick_goal_style(goal):

    if goal is None:
        return goal, False
    elif 'steps' in goal:
        if goal['steps'] < 20:
            return list(goal.keys())[0], goal['steps']
        else:
            raise OutOfLimitException(f"Goal steps higher than 20 steps: {goal['random steps']}")
    elif 'all answered' in goal:
        if isinstance(goal, dict):
            if goal['all answered']['export']:
                return list(goal.keys())[0], goal['all answered']['export']
            else:
                return list(goal.keys())[0], goal['all answered']['export']
        else:
            return goal, False

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
    is_starter: bool
    role: str
    context: Union[List[Union[str, Dict]], Dict, None]
    ask_about: list
    output: list
    conversations: list
    language: Union[str, None]
    test_name: str


class RoleData:

    def __init__(self, yaml_file):
        self.yaml = yaml_file

        try:
            self.validated_data = RoleDataModel(**self.yaml)
        except ValidationError as e:
            print(e.json())
            raise

        self.fallback = self.validated_data.fallback
        self.temperature = self.validated_data.temperature
        self.is_starter = self.validated_data.is_starter
        self.role = self.validated_data.role
        self.context = self.context_processor(self.validated_data.context)  # list
        self.ask_about = AskAboutClass(self.validated_data.ask_about)  # list
        self.output = self.validated_data.output  # dict

        conversation = self.list_to_dict_reformat(self.validated_data.conversations)

        self.conversation_number = conversation['number']
        self.goal_style = pick_goal_style(conversation['goal_style'])  # list
        self.language = set_language(self.validated_data.language)  # str
        self.interaction_styles = self.pick_interaction_style(conversation['interaction_style'])  # list
        self.test_name = self.validated_data.test_name  # str

    def reset_attributes(self):
        self.fallback = self.validated_data.fallback
        self.temperature = self.validated_data.temperature
        self.is_starter = self.validated_data.is_starter
        self.role = self.validated_data.role
        self.context = self.context_processor(self.validated_data.context)  # list
        self.ask_about.reset()  # self.picked_elements = [], self.phrases = []

        conversation = self.list_to_dict_reformat(self.validated_data.conversations)
        self.goal_style = pick_goal_style(conversation['goal_style'])  # list
        self.language = set_language(self.validated_data.language)  # str
        self.interaction_styles = self.pick_interaction_style(conversation['interaction_style'])  # list

    @staticmethod
    def list_to_dict_reformat(conv):
        result_dict = {k: v for d in conv for k, v in d.items()}
        return result_dict

    @staticmethod
    def personality_extraction(context):
        if context["personality"]:
            path = Path(context["personality"])
            if path.exists() and path.is_file():
                personality = read_yaml(path)
                try:
                    return personality['context']
                except KeyError:
                    raise InvalidFormat(f"Key 'context' not found in personality file")
        else:
            raise InvalidDataType("Data for context is not a dictionary with context key.")

    def context_processor(self, context):
        if isinstance(context, dict):
            personality_phrases = self.personality_extraction(context)
            return list_to_str(personality_phrases)

        res = len(list(filter(lambda x: isinstance(x, dict), context)))
        if res > 1:
            raise InvalidFormat(f"Too many keys in context list.")
        elif res <= 0 and not isinstance(context, dict):
            return list_to_str(context)
        else:
            custom_phrases = []
            personality_phrases = []
            for item in context:
                if isinstance(item, str):
                    custom_phrases.append(item)
                elif isinstance(item, dict):
                    personality_phrases = personality_phrases + self.personality_extraction(item)
                else:
                    raise InvalidDataType(f'Invalid data type in context list: {type(item)}:{item}')
            total_phrases =  personality_phrases + custom_phrases
            return list_to_str(total_phrases)

    def get_interaction_metadata(self):
        metadata_list = []
        for inter in self.interaction_styles:
            metadata_list.append(inter.get_metadata())

        return metadata_list

    def pick_interaction_style(self, interactions):

        inter_styles = {
            'long phrases': LongPhrases(),
            'change your mind': ChangeYourMind(),
            'change language': ChangeLanguage(self.language),
            'make spelling mistakes': MakeSpellingMistakes(),
            'single question': SingleQuestions(),
            'all questions': AllQuestions(),
            'default': Default()
        }

        def choice_styles(interaction_styles):
            count = random.randint(1, len(interaction_styles))
            random_list = random.sample(interaction_styles, count)
            logging.getLogger().verbose(f'interaction style amount: {count} style(s): {random_list}')
            return random_list

        def get_styles(interact):
            interactions_list = []
            try:
                for inter in interact:

                    if isinstance(inter, dict):
                        keys = list(inter.keys())
                        if keys[0] == "change language":
                            cl_interaction = inter_styles[keys[0]]
                            cl_interaction.languages_options = inter.get(keys[0]).copy()
                            cl_interaction.change_language_flag = True
                            interactions_list.append(cl_interaction)

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
            interaction_def = inter_styles['default']
            return [interaction_def]

        elif isinstance(interactions[0], dict) and 'random' in list(interactions[0].keys()):
            # todo: add validation funct to admit random only if it's alone in the list
            # inter_keys = list(interactions[0].keys())

            # if 'random' in inter_keys:
            inter_rand = interactions[0]['random']
            choice = choice_styles(inter_rand)
            return get_styles(choice)

        else:
            return get_styles(interactions)

    def get_language(self):

        for instance in self.interaction_styles:
            if instance.change_language_flag:
                prompt = instance.get_prompt()
                return prompt

        return f"Please, talk in {self.language}"
