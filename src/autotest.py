import requests
import configparser
import logging
from argparse import ArgumentParser

# Definir el nuevo nivel VERBOSE
VERBOSE_LEVEL_NUM = 15
logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")


def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_LEVEL_NUM):
        self._log(VERBOSE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.verbose = verbose

from colorama import Fore, Style
from collections import OrderedDict
from user_sim.role_structure import *
from user_sim.utils.utilities import *
from user_sim.user_simulator import user_generation
from user_sim.data_extraction import data_extraction


class Chatbot:
    def __init__(self, url):
        self.url = url
        self.fallback = 'I do not understand you'

    def execute_with_input(self, user_msg):
        return ''


class ChatbotRasa(Chatbot):
    def execute_with_input(self, user_msg):
        new_data = {
            "sender": "user",
            "message": user_msg
        }
        post_response = requests.post(self.url, json=new_data)
        post_response_json = post_response.json()
        if len(post_response_json) > 0:
            return post_response_json[0].get('text')
        else:
            return ''


class ChatbotTaskyto(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.id = None

    def execute_with_input(self, user_msg):
        if self.id == None:
            post_response = requests.post(self.url + '/conversation/new')
            post_response_json = post_response.json()
            self.id = post_response_json.get('id')

        if self.id != None:
            new_data = {
                "id": self.id,
                "message": user_msg
            }
            try:
                post_response = requests.post(self.url + '/conversation/user_message', json=new_data)
                post_response_json = post_response.json()
                return post_response_json.get('message')
            except requests.exceptions.JSONDecodeError as e:
                logging.getLogger().verbose(f"Couldn't get response from the server: {e}")
                return 'exit'

        return ''


def print_user(msg): print(f"{Fore.GREEN}User:{Style.RESET_ALL} {msg}")


def print_chatbot(msg): print(f"{Fore.LIGHTRED_EX}Chatbot:{Style.RESET_ALL} {msg}")


def get_conversation_metadata(user_profile, the_user, serial=None):
    def conversation_metadata(up):
        interaction_style_list = []
        conversation_list = []

        for inter in up.interaction_styles:
            interaction_style_list.append(inter.get_metadata())

        for conv in user_profile.yaml['conversations']:
            keys = list(conv.keys())
            if keys[0] == 'interaction_style':
                conversation_list.append({'interaction_style': interaction_style_list})

            elif keys[0] == 'goal_style':
                if 'random steps' in conv[keys[0]]:
                    conversation_list.append({keys[0]: {'steps': user_profile.goal_style[1]}})
                else:
                    conversation_list.append(conv)

            else:
                conversation_list.append(conv)

        return conversation_list

    def ask_about_metadata(up):
        if not up.ask_about.variable_list:
            return up.ask_about.str_list

        return user_profile.ask_about.str_list + user_profile.ask_about.picked_elements

    def data_output_extraction(user_profile, the_user):
        output_list = user_profile.output
        data_list = []

        for output in output_list:
            var_name = list(output.keys())[0]
            var_dict = output.get(var_name)
            my_data_extract = data_extraction(the_user.conversation_history,
                                              var_name,
                                              var_dict["type"],
                                              var_dict["description"])
            data_list.append(my_data_extract.get_data_extraction())

        return data_list

    data_output = {'data_output': data_output_extraction(user_profile, the_user)}
    ask_about = {'ask_about': ask_about_metadata(user_profile)}
    conversation = {'conversation': conversation_metadata(user_profile)}
    language = {'language': user_profile.yaml['language']}
    serial_dict = {'serial': serial}

    metadata = {**serial_dict,
                **language,
                **ask_about,
                **conversation,
                ** data_output
                }

    # metadata = OrderedDict([
    #     ('ask_about', ask_about_metadata(user_profile)),
    #     ('conversation', conversation_metadata(user_profile)),
    #     ('data_output', data_output_extraction(user_profile, the_user)),
    #     ('language', user_profile.yaml['language']),
    #     ('serial', serial),
    #
    # ])

    return metadata


def check_keys(key_list: list):
    if os.path.exists("keys.properties"):
        logging.getLogger().verbose("properties found!")
        config = configparser.ConfigParser()
        config.read('keys.properties')

        # Loop over all keys and values
        for key in config['keys']:
            key = key.upper()
            os.environ[key] = config['keys'][key]

    for k in key_list:
        if not os.environ.get(k):
            raise Exception(f"{k} not found")


def generate(technology, chatbot, user, extract):
    user_profile = role_data(user)
    serial = generate_serial()

    for i in range(user_profile.conversation_number):
        if technology == 'rasa':
            the_chatbot = ChatbotRasa(chatbot)
        elif technology == 'taskyto':
            the_chatbot = ChatbotTaskyto(chatbot)
        else:
            the_chatbot = Chatbot(chatbot)

        the_chatbot.fallback = user_profile.fallback
        the_user = user_generation(user_profile, the_chatbot)
        starter = user_profile.isstarter

        while True:
            if starter:
                user_msg = the_user.open_conversation()
                print_user(user_msg)

                response = the_chatbot.execute_with_input(user_msg)
                if response == 'exit':
                    logging.getLogger().verbose('The server cut the conversation. End.')
                    break
                print_chatbot(response)

                starter = False

            user_msg = the_user.get_response(response)

            if user_msg == "exit":
                logging.getLogger().verbose('exit')
                break

            else:
                # configure parameter "user starts?"
                print_user(user_msg)
                response = the_chatbot.execute_with_input(user_msg)
                print_chatbot(response)

        if extract:
            history = the_user.conversation_history
            metadata = get_conversation_metadata(user_profile, the_user, serial)
            test_name = user_profile.test_name

            user_profile.reset_attributes()
            save_test_conv(history, metadata, test_name, extract, serial, counter=i)
            # the_user.save_data_gathering(extract)


if __name__ == '__main__':
    parser = ArgumentParser(description='Conversation generator for a chatbot')
    parser.add_argument('--technology', required=True, choices=['rasa', 'taskyto'],
                        help='Technology the chatbot is implemented in')
    parser.add_argument('--chatbot', required=True, help='URL where the chatbot is deployed')
    parser.add_argument('--user', required=True, help='User profile to test the chatbot')
    parser.add_argument("--extract", default=False, help='Path to store conversation user-chatbot')
    parser.add_argument('--verbose', action='store_true', help='Shows debug prints')
    args = parser.parse_args()

    #logging config
    # logging_level = VERBOSE_LEVEL_NUM if args.verbose else logging.INFO
    if args.verbose:
        logging_level = VERBOSE_LEVEL_NUM
        logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # logging.info("Iniciando el generador de conversaciones")
    logging.debug(f"Argumentos recibidos: {args}")
    logging.getLogger().verbose('verbose enabled')

    check_keys(["OPENAI_API_KEY"])
    generate(args.technology, args.chatbot, args.user, args.extract)
