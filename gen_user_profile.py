import glob
import inflect
from argparse import ArgumentParser
from typing import List, Dict

from user_sim.role_structure import *


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args1, **kwargs1):
        return super().increase_indent(flow=flow, indentless=False)


class ConversationConfiguration:
    def __init__(self,
                 number_conversations: int = 1,
                 steps_in_conversation: int = 1,
                 interaction_style: List[str] = [],
                 change_language: List[str] = []
                 ):
        self.number = number_conversations
        self.steps = steps_in_conversation
        self.interaction_style = interaction_style
        self.change_language = change_language

    def to_dict(self):
        interaction_to_dict = [style for style in self.interaction_style]
        if len(self.change_language):
            interaction_to_dict.append({"change language": self.change_language})
        return [
            {"number": self.number},
            {"goal_style": {"steps": self.steps}},
            {"interaction_style": interaction_to_dict}
        ]


class RoleData (role_data):
    def __init__(self,
                 temperature: float = 0.8,
                 isstarter: bool = True,
                 fallback: str = '',
                 role: str = '',
                 context: List[str] = None,
                 ask_about: List[str | Dict] = [],
                 conversations: ConversationConfiguration = ConversationConfiguration(),
                 language: str = 'English',
                 test_name: str = ''
                 ):
        self.temperature = temperature
        self.isstarter = isstarter
        self.fallback = fallback
        self.role = role
        self.context = context
        self.ask_about = ask_about
        self.conversations = conversations
        self.language = language
        self.test_name = test_name

    def to_dict(self) -> dict:
        ret = self.__dict__
        ret['conversations'] = self.conversations.to_dict()
        return ret

    def to_yaml(self, file):
        with open(file, 'w') as outfile:
            yaml.dump(self.to_dict(), outfile, default_flow_style=False, sort_keys=False, Dumper=Dumper)


class SpecificationTaskyto:
    @staticmethod
    def __load_chatbot_modules(chatbot_folder) -> List[Dict]:
        """
        :param chatbot_folder: folder containing the chatbot modules
        :returns yaml files in chatbot_folder
        """
        modules = []
        for file_path in glob.glob(os.path.join(chatbot_folder, '*.yaml')):
            with open(file_path) as yaml_file:
                modules.append(yaml.safe_load(yaml_file.read()))
        return modules

    @staticmethod
    def __load_configuration_file(chatbot_folder) -> Dict:
        """
        :param chatbot_folder: folder containing the chatbot modules
        :returns file chatbot_folder/configuration/default.yaml
        """
        configuration_file = os.path.join(chatbot_folder, "configuration", "default.yaml")
        if os.path.isfile(configuration_file):
            with open(configuration_file) as yaml_file:
                return yaml.safe_load(yaml_file.read())
        return {}

    def build_user_profile(self, chatbot_folder) -> RoleData:
        """
        :param chatbot_folder: folder containing the chatbot modules
        :returns user profile built from the chatbot specification
        """
        formatter = inflect.engine()
        profile = RoleData()
        profile.role = 'You have to act as a user of a chatbot.'
        profile.context = [
                 "Never indicate that you are the user, like 'user: bla bla'.",
                 "Sometimes, interact with what the assistant just said.",
                 "Never act as the assistant.",
                 "Don't end the conversation until you've asked everything you need."
             ]
        # profile.conversations.interaction_style.append('long phrase')
        profile.conversations.interaction_style.append('change your mind')
        profile.conversations.interaction_style.append('make spelling mistakes')
        profile.conversations.interaction_style.append('single question')
        profile.conversations.interaction_style.append('all questions')
        # profile.conversations.interaction_style.append('default')

        # chatbot modules
        modules = __class__.__load_chatbot_modules(chatbot_folder)
        for module in modules:
            if module.get("modules"):
                modules.extend(module.get("modules"))
                continue
            # menu module ...........................................
            kind = module.get("kind")
            if kind == "menu":
                if module.get("items"):
                    modules.extend(module.get("items"))
                if not profile.fallback:
                    profile.fallback = module.get("fallback")
                if module.get("presentation"):
                    profile.role += f' This chatbot is described as follows: \"{module.get("presentation").strip()}\"'
            # data gathering module .................................
            elif kind == "data_gathering":
                for data in module.get("data"):
                    for item in data.keys():
                        item_values = data.get(item)
                        if item_values.get("type") == "enum":
                            if formatter.singular_noun(item) is True:
                                item = formatter.plural(item)
                            ask_about = 'Consider the following ' + item + ': {{' + item + '}}.'
                            ask_values = __class__.__flatten(item_values.get("values"))
                            profile.ask_about.append(ask_about)
                            profile.ask_about.append({item: ask_values})
            # answer module .........................................
            elif kind == "answer":
                profile.ask_about.append(module.get("title"))

        # chatbot configuration
        config = __class__.__load_configuration_file(chatbot_folder)
        if config.get("languages"):
            languages = [language.strip() for language in config.get("languages").split(",")]
            profile.conversations.change_language.extend(languages)
            profile.language = languages[0]

        return profile

    @staticmethod
    def __flatten(list_values: List[str | Dict[str, List[str]]]) -> List[str]:
        """
        :param list_values: list of values, which can be strings or dictionaries
        :return: list of string values (dicts are flattened -- their keys and values are added to the list)
        """
        list_flattened = []
        for value in list_values:
            if isinstance(value, Dict):
                for key in value.keys():
                    list_flattened.append(key)
                    list_flattened.extend(value.get(key))
            else:
                list_flattened.append(value)
        return list_flattened


def generate(technology: str, chatbot: str, user: str):
    chatbot_spec = None
    if technology == 'taskyto':
        chatbot_spec = SpecificationTaskyto()

    if chatbot_spec:
        user_profile = chatbot_spec.build_user_profile(chatbot_folder=chatbot)
        chatbot_name = os.path.basename(chatbot)
        test_name = f"{chatbot_name}_test"
        user_profile.test_name = test_name
        if user:
            user_profile_name = f"{user}{os.sep}{chatbot_name}_user_profile.yaml"
        else:
            user_profile_name = f"{chatbot}{os.sep}{chatbot_name}_user_profile.yaml"
        print(f"The following user profile has been created: {user_profile_name}")
        user_profile.to_yaml(user_profile_name)


if __name__ == '__main__':
    parser = ArgumentParser(description='User profile generator from a chatbot specification')
    parser.add_argument('--technology', required=True, choices=['taskyto'], help='Technology the chatbot is implemented in')
    parser.add_argument('--chatbot', required=True, help='Folder that contains the chatbot specification')
    parser.add_argument('--user', required=False, help='Folder to store the user profile (the chatbot folder if none is given)')
    args = parser.parse_args()

    generate(args.technology, args.chatbot, args.user)
