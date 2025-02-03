from pydantic import BaseModel, ValidationError, field_validator, validator
from typing import List, Union, Dict, Optional
from .interaction_styles import *
from .ask_about import *
from .utils.exceptions import *
from .utils.languages import languages
from .utils import cost_estimation
from .utils import config
from pathlib import Path

import logging
logger = logging.getLogger('Info Logger')


def pick_goal_style(goal):

    if goal is None:
        return goal, False

    if 'max_cost' in goal:
        if goal['max_cost'] > 0:
            config.limit_individual_cost = goal['max_cost']
            config.token_count_enabled = True
        else:
            raise NoCostException(f"Goal cost can't be lower than or equal to 0: {goal['cost']}")
    else:
        config.limit_individual_cost = config.limit_cost

    if 'steps' in goal:
        if goal['steps'] <= 20 or goal['steps'] > 0:
            return list(goal.keys())[0], goal['steps']
        else:
            raise OutOfLimitException(f"Goal steps higher than 20 steps or lower than 0 steps: {goal['steps']}")

    elif 'all_answered' in goal or 'default' in goal:
        if isinstance(goal, dict):

            if 'export' in goal['all_answered']:
                all_answered_goal = [list(goal.keys())[0], goal['all_answered']['export']]
            else:
                all_answered_goal = [list(goal.keys())[0], False]

            if 'limit' in goal['all_answered']:
                all_answered_goal.append(goal['all_answered']['limit'])
            else:
                all_answered_goal.append(30)

            return all_answered_goal
        else:
            return [goal, False, 30]

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
        logger.info("Language parameter empty. Setting language to Default (English)")
        return "English"
    try:
        if lang in languages:
            logger.info(f"Language set to {lang}")
            return lang
        else:
            raise InvalidLanguageException(f'Invalid language input: {lang}. Setting language to default (English)')
    except InvalidLanguageException as e:
        return "English"


def list_to_str(list_of_strings):
    if list_of_strings is None:
        return ''
    try:
        single_string = ' '.join(list_of_strings)
        return single_string
    except Exception as e:
        # logging.getLogger().verbose(f'Error: {e}')
        return ''


class ConvFormat(BaseModel):
    type: Optional[str] = "text"
    config: Optional[str] = None

class LLM(BaseModel):
    model: Optional[str] = "gpt-4o"
    temperature: Optional[float] = 0.8
    format: Optional[ConvFormat] = ConvFormat()  # text, speech, hybrid

class User(BaseModel):
    language: Optional[Union[str, None]] = 'English'
    role: str
    context: Optional[Union[List[Union[str, Dict]], Dict, None]] = ''
    goals: list


class Chatbot(BaseModel):
    is_starter: Optional[bool] = True
    fallback: str
    output: list


class Conversation(BaseModel):
    number: Union[int, str]
    max_cost: Optional[float]=10**9
    goal_style: Dict
    interaction_style: list

    @field_validator('max_cost', mode='before')
    @classmethod
    def set_token_count_enabled(cls, value):
        if value is not None:
            config.token_count_enabled = True
        return value

class RoleDataModel(BaseModel):
    test_name: str
    llm: Optional[LLM] = LLM()
    user: User
    chatbot: Chatbot
    conversation: Conversation


class RoleData:

    def __init__(self, yaml_file, personality_file):
        self.yaml = yaml_file
        self.personality_file = personality_file

        try:
            self.validated_data = RoleDataModel(**self.yaml)
        except ValidationError as e:
            print(e.json())
            raise

    #Test Name
        self.test_name = self.validated_data.test_name

    #LLM
        self.model = self.validated_data.llm.model
        self.temperature = self.validated_data.llm.temperature
        self.format_type = self.validated_data.llm.format.type
        self.format_config = self.validated_data.llm.format.config

    #User
        self.language = set_language(self.validated_data.user.language)
        self.role = self.validated_data.user.role
        self.raw_context = self.validated_data.user.context
        self.context = self.context_processor(self.raw_context)
        self.personality = None
        self.ask_about = AskAboutClass(self.validated_data.user.goals)

    #Chatbot
        self.is_starter = self.validated_data.chatbot.is_starter
        self.fallback = self.validated_data.chatbot.fallback
        self.output = self.validated_data.chatbot.output

    #Conversation
        self.conversation_number = self.get_conversation_number(self.validated_data.conversation.number)
        self.max_cost = self.validated_data.conversation.max_cost
        self.goal_style = pick_goal_style(self.validated_data.conversation.goal_style)
        self.interaction_styles = self.pick_interaction_style(self.validated_data.conversation.interaction_style)

    cost_estimation.initialize_class()


    def reset_attributes(self):
        logger.info(f"Preparing attributes for next conversation...")
        self.fallback = self.validated_data.chatbot.fallback
        # self.is_starter = self.validated_data.is_starter
        self.context = self.context_processor(self.raw_context)
        self.ask_about.reset()  # self.picked_elements = [], self.phrases = []

        self.goal_style = pick_goal_style(self.validated_data.conversation.goal_style)
        self.language = set_language(self.validated_data.user.language)
        self.interaction_styles = self.pick_interaction_style(self.validated_data.conversation.interaction_style)

    @staticmethod
    def list_to_dict_reformat(conv):
        result_dict = {k: v for d in conv for k, v in d.items()}
        return result_dict


    def personality_extraction(self, context):
        if context["personality"]:
            path = Path(context["personality"])
            if path.exists() and path.is_file():
                personality = read_yaml(context["personality"])
                try:
                    self.personality = personality["name"]
                    return personality['context']
                except KeyError:
                    raise InvalidFormat(f"Key 'context' not found in personality file")
        else:
            raise InvalidDataType("Data for context is not a dictionary with context key.")

    def get_conversation_number(self, conversation):
        if isinstance(conversation, int):
            return conversation
        elif conversation == "all_combinations":
            if self.ask_about.combinations <= 0:
                logger.error("Conversation number set to 'all_combinations' but no combinations can be made.")
            return self.ask_about.combinations
        elif "sample(" in conversation:
            pattern = r'sample\((.*?)\)'
            percentage = float(re.findall(pattern, conversation)[0])
            sample = round(self.ask_about.combinations * percentage)

            if sample <= 0:
                logger.error("Conversation number set to 'sample' but the fraction obtained is 0.")
            return sample

    def context_processor(self, context):
        if isinstance(context, dict):
            personality_phrases = self.personality_extraction(context)
            return list_to_str(personality_phrases)

        res = len(list(filter(lambda x: isinstance(x, dict), context)))
        if res > 1:
            raise InvalidFormat(f"Too many keys in context list.")
        elif res <= 0 and not isinstance(context, dict):
            phrases = list_to_str(context)
            if self.personality_file is not None:
                personality = read_yaml(self.personality_file)
                personality_phrases = personality['context']
                phrases = phrases + list_to_str(personality_phrases)
            return phrases
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

            # If no personality is given, we use the one specified as input in the command line
            if len(personality_phrases) == 0 and self.personality_file is not None:
                personality = read_yaml(self.personality_file)
                personality_phrases = personality['context']

            total_phrases = personality_phrases + custom_phrases
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
            # logging.getLogger().verbose(f'interaction style amount: {count} style(s): {random_list}')
            logger.info(f'interaction style count: {count}; style(s): {random_list}')
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
