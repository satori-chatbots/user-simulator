import requests
from colorama import Fore, Style
from user_sim.role_structure import *
from user_sim.utils.utilities import *
from user_sim.user_simulator import UserGeneration
from user_sim.data_extraction import DataExtraction
import logging
from argparse import ArgumentParser
import timeit
from datetime import timedelta

# Define new level "verbose"
VERBOSE_LEVEL_NUM = 15
logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")


def verbose(self, message, *args, **kwargs):
    if self.isEnabledFor(VERBOSE_LEVEL_NUM):
        self._log(VERBOSE_LEVEL_NUM, message, args, **kwargs)


logging.Logger.verbose = verbose


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
        if self.id is None:
            post_response = requests.post(self.url + '/conversation/new')
            post_response_json = post_response.json()
            self.id = post_response_json.get('id')

        if self.id is not None:
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

    def data_output_extraction(u_profile, user):
        output_list = u_profile.output
        data_list = []

        for output in output_list:
            var_name = list(output.keys())[0]
            var_dict = output.get(var_name)
            my_data_extract = DataExtraction(user.conversation_history,
                                             var_name,
                                             var_dict["type"],
                                             var_dict["description"])
            data_list.append(my_data_extract.get_data_extraction())

        return data_list

    data_output = {'data_output': data_output_extraction(user_profile, the_user)}
    ask_about = {'ask_about': ask_about_metadata(user_profile)}
    conversation = {'conversation': conversation_metadata(user_profile)}
    language = {'language': user_profile.yaml['language'] if user_profile.yaml['language'] else 'English'}
    serial_dict = {'serial': serial}

    metadata = {**serial_dict,
                **language,
                **ask_about,
                **conversation,
                **data_output
                }

    return metadata


def generate(technology, chatbot, user, extract):
    user_profile = RoleData(user)
    serial = generate_serial()

    start_time_test = timeit.default_timer()
    for i in range(user_profile.conversation_number):
        start_time_conversation = timeit.default_timer()
        if technology == 'rasa':
            the_chatbot = ChatbotRasa(chatbot)
        elif technology == 'taskyto':
            the_chatbot = ChatbotTaskyto(chatbot)
        else:
            the_chatbot = Chatbot(chatbot)

        the_chatbot.fallback = user_profile.fallback
        the_user = UserGeneration(user_profile, the_chatbot)
        starter = user_profile.is_starter

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
            end_time_conversation = timeit.default_timer()
            conversation_time = end_time_conversation - start_time_conversation
            formatted_time_conv = str(timedelta(seconds=conversation_time))
            print(f"Conversation Time: {formatted_time_conv}")
            user_profile.reset_attributes()
            save_test_conv(history, metadata, test_name, extract, serial, formatted_time_conv, counter=i)
            # the_user.save_data_gathering(extract)

    end_time_test = timeit.default_timer()
    execution_time = end_time_test - start_time_test
    formatted_time = str(timedelta(seconds=execution_time))
    print(f"Execution Time: {formatted_time}")

if __name__ == '__main__':
    parser = ArgumentParser(description='Conversation generator for a chatbot')
    parser.add_argument('--technology', required=True, choices=['rasa', 'taskyto'],
                        help='Technology the chatbot is implemented in')
    parser.add_argument('--chatbot', required=True, help='URL where the chatbot is deployed')
    parser.add_argument('--user', required=True, help='User profile to test the chatbot')
    parser.add_argument("--extract", default=False, help='Path to store conversation user-chatbot')
    parser.add_argument('--verbose', action='store_true', help='Shows debug prints')
    args = parser.parse_args()

    # logging_level = VERBOSE_LEVEL_NUM if args.verbose else logging.INFO
    if args.verbose:
        logging_level = VERBOSE_LEVEL_NUM
        logging.basicConfig(level=logging_level, format='%(asc_time)s - %(level_name)s - %(message)s')

    logging.debug(f"Received arguments: {args}")
    logging.getLogger().verbose('verbose enabled')

    check_keys(["OPENAI_API_KEY"])
    generate(args.technology, args.chatbot, args.user, args.extract)
