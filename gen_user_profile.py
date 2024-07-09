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
                 interaction_style: str = None,
                 change_language: List[str] = None
                 ):
        self.number = number_conversations
        self.steps = steps_in_conversation
        self.interaction_style = interaction_style
        self.change_language = change_language

    def to_dict(self):
        return [
            {"number": self.number},
            {"goal_style": [{"steps": self.steps}]},
            {"interaction_style": [
                    self.interaction_style,
                    {"change language": self.change_language}
                ]}
        ]


class RoleData (role_data):
    def __init__(self,
                 temperature: float = 0.8,
                 isstarter: bool = True,
                 fallback: str = '',
                 role: str = '',
                 context: List[str] = None,
                 ask_about: List[str | Dict] = None,
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
    def build_user_profile(chatbot_file) -> RoleData:
        data = dict()
        with open(chatbot_file) as yaml_file:
            data = yaml.safe_load(yaml_file.read())

        profile = RoleData()
        modules = data.get("modules")
        if modules:
            for module in modules:
                if not profile.fallback:
                    profile.fallback = module.get("fallback")

        return profile

        # return RoleData(
        #     temperature=0.8, # ---------------------------------------------------------------------------------------
        #     isstarter=True, # ----------------------------------------------------------------------------------------
        #     fallback="can you say that again?", # --------------------------------------------------------------------
        #     role="you have to act as a user ordering a pizza to a pizza shop.",
        #     context=[
        #         "never indicate that you are the user, like 'user: bla bla'",
        #         "Sometimes, interact with what the assistant just said.",
        #         "Never act as the assistant.",
        #         "Don't end the conversation until you've asked everything you need."
        #     ],
        #     ask_about=[
        #         "a pizza with any size of the following: {{size}}",
        #         {"size": ['small', 'medium', 'large', 'extra large']},
        #         "any of the following for toppings: {{toppings}}",
        #         {"toppings": ['mushrooms', 'tomato', 'onion', 'cheese']}
        #     ],
        #     conversations=ConversationConfiguration(
        #         number_conversations=1,
        #         steps_in_conversation=1,
        #         interaction_style='make spelling mistakes',
        #         change_language=['italian', 'portuguese']
        #     ),
        #     language="English",
        #     test_name="pizza_order_test"
        # )


def generate(technology, chatbot, user):
    if technology == 'taskyto':
        user_profile = SpecificationTaskyto.build_user_profile(chatbot_file=chatbot)
        user_profile.to_yaml(user)


if __name__ == '__main__':
    parser = ArgumentParser(description='User profile generator from a chatbot specification')
    parser.add_argument('--technology', required=True, choices=['taskyto'], help='Technology the chatbot is implemented in')
    parser.add_argument('--chatbot', required=True, help='File path that contains the chatbot specification')
    parser.add_argument('--user', required=True, help='File path to store the user profile')
    args = parser.parse_args()

    generate(args.technology, args.chatbot, args.user)
