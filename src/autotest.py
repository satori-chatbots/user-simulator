import time
import timeit
from argparse import ArgumentParser
from user_sim.utils import config
from codecs import ignore_errors

from pygame.display import update

from user_sim.utils.utilities import check_keys
import yaml

check_keys(["OPENAI_API_KEY"])


from colorama import Fore, Style
from technologies.chatbot_connectors import (Chatbot, ChatbotRasa, ChatbotTaskyto, ChatbotAdaUam, ChatbotMillionBot,
                                             ChatbotLolaUMU, ChatbotServiceform, KukiChatbot, JulieChatbot, ChatbotCatalinaRivas, ChatbotSaicMalaga, \
    ChatbotGenion)
from user_sim.data_extraction import DataExtraction
from user_sim.role_structure import *
from user_sim.user_simulator import UserSimulator
from user_sim.utils.show_logs import *
from user_sim.utils.utilities import *
from user_sim.utils.token_cost_calculator import create_cost_dataset


def print_user(msg):
    clean_text = re.sub(r'\(Image description[^)]*\)', '', msg)
    clean_text = re.sub(r'\(PDF content: [^)]*>>\)', '', clean_text)
    print(f"{Fore.GREEN}User:{Style.RESET_ALL} {clean_text}")


def print_chatbot(msg):
    clean_text = re.sub(r'\(Image description[^)]*\)', '', msg)
    clean_text = re.sub(r'\(PDF content:.*?\>\>\)', '', clean_text, flags=re.DOTALL)
    print(f"{Fore.LIGHTRED_EX}Chatbot:{Style.RESET_ALL} {clean_text}")


def get_conversation_metadata(user_profile, the_user, serial=None):
    def conversation_metadata(up):
        interaction_style_list = []
        conversation_list = []

        for inter in up.interaction_styles:
            interaction_style_list.append(inter.get_metadata())

        conversation_list.append({'interaction_style': interaction_style_list})

        if isinstance(up.yaml['conversation']['number'], int):
            conversation_list.append({'number': up.yaml['conversation']['number']})
        else:
            conversation_list.append({'number': up.conversation_number})

        if 'random steps' in up.yaml['conversation']['goal_style']:
            conversation_list.append({'goal_style': {'steps': up.goal_style[1]}})
        else:
            conversation_list.append(up.yaml['conversation']['goal_style'])

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

        data_dict = {k: v for dic in data_list for k, v in dic.items()}
        has_none = any(value is None for value in data_dict.values())
        if has_none:
            count_none = sum(1 for value in data_dict.values() if value is None)
            config.errors.append({1001: f"{count_none} goals left to complete."})

        return data_list

    def total_cost_calculator():
        encoding = get_encoding(config.cost_ds_path)["encoding"]
        cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)

        total_sum_cost = cost_df[cost_df["Conversation"]==config.conversation_name]['Total Cost'].sum()
        total_sum_cost = round(float(total_sum_cost), 8)

        return total_sum_cost


    data_output = {'data_output': data_output_extraction(user_profile, the_user)}
    context = {'context': user_profile.raw_context}
    ask_about = {'ask_about': ask_about_metadata(user_profile)}
    conversation = {'conversation': conversation_metadata(user_profile)}
    language = {'language': user_profile.language}
    serial_dict = {'serial': serial}
    errors_dict = {'errors': config.errors}
    total_cost = {'total_cost($)': total_cost_calculator()}
    metadata = {**serial_dict,
                **language,
                **context,
                **ask_about,
                **conversation,
                **data_output,
                **errors_dict,
                **total_cost
                }

    return metadata


def parse_profiles(user_path):
    def is_yaml(file):
        if not file.endswith(('.yaml', '.yml')):
            return False
        try:
            with open(file, 'r') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError:
            return False

    list_of_files = []
    if os.path.isfile(user_path):
        if is_yaml(user_path):
            yaml_file = read_yaml(user_path)
            return [yaml_file]
        else:
            raise Exception(f'The user profile file is not a yaml: {user_path}')
    elif os.path.isdir(user_path):
        for root, _, files in os.walk(user_path):
            for file in files:
                if is_yaml(os.path.join(root, file)):
                    path = root + '/' + file
                    yaml_file = read_yaml(path)
                    list_of_files.append(yaml_file)

            return list_of_files
    else:
        raise Exception(f'Invalid path for user profile operation: {user_path}')


def build_chatbot(technology, *args, **kwargs) -> Chatbot:
    chatbot_builder = {
        'rasa': ChatbotRasa,
        'taskyto': ChatbotTaskyto,
        'ada-uam': ChatbotAdaUam,
        'millionbot': ChatbotMillionBot,
        'lola': ChatbotLolaUMU,
        'rivas_catalina': ChatbotCatalinaRivas,
        'saic_malaga': ChatbotSaicMalaga,
        'serviceform': ChatbotServiceform,
        'kuki': KukiChatbot,
        'julie': JulieChatbot,
        'genion': ChatbotGenion
    }
    chatbot_class = chatbot_builder.get(technology, Chatbot)
    return chatbot_class(*args, **kwargs)



def generate_conversation(technology, chatbot, user,
                          personality, extract, clean_cache,
                          ignore_cache, update_cache):
    profiles = parse_profiles(user)
    serial = generate_serial()
    config.serial = serial
    create_cost_dataset(serial, extract)
    my_execution_stat = ExecutionStats(extract, serial)
    the_chatbot = build_chatbot(technology, chatbot, ignore_cache=ignore_cache, update_cache=update_cache)


    for profile in profiles:
        user_profile = RoleData(profile, personality)
        test_name = user_profile.test_name
        config.test_name = test_name
        chat_format = user_profile.format_type
        start_time_test = timeit.default_timer()

        for i in range(user_profile.conversation_number):
            config.conversation_name = f'{i}_{test_name}_{serial}.yml'
            the_chatbot.fallback = user_profile.fallback
            the_user = UserSimulator(user_profile, the_chatbot)
            bot_starter = user_profile.is_starter
            response_time = []

            start_time_conversation = timeit.default_timer()
            response = ''

            if chat_format == "speech":
                from user_sim.stt_module import STTModule

                stt = STTModule(user_profile.format_config)

                def send_user_message(user_msg):
                    print_user(user_msg)
                    stt.say(user_msg)

                def get_chatbot_response(user_msg):
                    start_response_time = timeit.default_timer()
                    is_ok, response = stt.hear()
                    end_response_time = timeit.default_timer()
                    time_sec = timedelta(seconds=end_response_time - start_response_time).total_seconds()
                    response_time.append(time_sec)
                    return is_ok, response

                def get_chatbot_starter_response():
                    is_ok, response = stt.hear()
                    return is_ok, response

            elif chat_format == "text":

                if user_profile.format_config:
                    logger.warning("Chat format is text, but an SR configuration was provided. This configuration will"
                                   " be ignored.")

                def send_user_message(user_msg):
                    print_user(user_msg)

                def get_chatbot_response(user_msg):
                    start_response_time = timeit.default_timer()
                    is_ok, response = the_chatbot.execute_with_input(user_msg)
                    end_response_time = timeit.default_timer()
                    time_sec = timedelta(seconds=end_response_time - start_response_time).total_seconds()
                    response_time.append(time_sec)
                    return is_ok, response

                def get_chatbot_starter_response():
                    is_ok, response = the_chatbot.execute_starter_chatbot()
                    return is_ok, response

            while True:

                if not bot_starter:
                    user_msg = the_user.open_conversation()
                    send_user_message(user_msg)

                    is_ok, response = get_chatbot_response(user_msg)
                    if not is_ok:
                        if response is not None:
                            the_user.update_history("Assistant", "Error: " + response)
                        else:
                            the_user.update_history("Assistant", "Error: The server did not respond.")
                        break

                    print_chatbot(response)
                    bot_starter = True

                elif not the_user.conversation_history["interaction"]:
                    is_ok, response = get_chatbot_starter_response()
                    if not is_ok:
                        if response is not None:
                            the_user.update_history("Assistant", "Error: " + response)
                        else:
                            the_user.update_history("Assistant", "Error: The server did not respond.")
                        break
                    print_chatbot(response)
                    user_msg = the_user.open_conversation()


                user_msg = the_user.get_response(response)

                if user_msg == "exit":
                    break
                else:
                    send_user_message(user_msg)

                    is_ok, response = get_chatbot_response(user_msg)
                    if response == 'timeout':
                        break
                    print_chatbot(response)
                    if not is_ok:
                        if response is not None:
                            the_user.update_history("Assistant", "Error: " + response)
                        else:
                            the_user.update_history("Assistant", "Error: The server did not respond.")
                        break

            if extract:
                end_time_conversation = timeit.default_timer()
                conversation_time = end_time_conversation - start_time_conversation
                formatted_time_conv = timedelta(seconds=conversation_time).total_seconds()
                print(f"Conversation Time: {formatted_time_conv} (s)")

                history = the_user.conversation_history
                metadata = get_conversation_metadata(user_profile, the_user, serial)
                dg_dataframe = the_user.data_gathering.gathering_register
                csv_extraction = the_user.goal_style[1] if the_user.goal_style[0] == 'all_answered' else False
                answer_validation_data = (dg_dataframe, csv_extraction)
                save_test_conv(history, metadata, test_name, extract, serial,
                               formatted_time_conv, response_time, answer_validation_data, counter=i)

            user_profile.reset_attributes()

        end_time_test = timeit.default_timer()
        execution_time = end_time_test - start_time_test
        formatted_time = timedelta(seconds=execution_time).total_seconds()
        print(f"Execution Time: {formatted_time} (s)")
        print('------------------------------')

        if user_profile.conversation_number > 0:
            my_execution_stat.add_test_name(test_name)
            my_execution_stat.show_last_stats()


    if clean_cache:
        the_chatbot.clean_temp_files()

    if extract and len(my_execution_stat.test_names) == len(profiles):
        my_execution_stat.show_global_stats()
        my_execution_stat.export_stats()
    elif extract:
        logger.warning("Stats export was enabled but couldn't retrieve all stats. No stats will be exported.")
    else:
        pass


if __name__ == '__main__':
    parser = ArgumentParser(description='Conversation generator for a chatbot')
    parser.add_argument('--technology', required=True,
                        choices=['rasa', 'taskyto', 'ada-uam', 'millionbot', 'genion', 'lola', 'serviceform', 'kuki', 'julie', 'rivas_catalina', 'saic_malaga'],
                        help='Technology the chatbot is implemented in')
    parser.add_argument('--chatbot', required=True, help='URL where the chatbot is deployed')
    parser.add_argument('--user', required=True, help='User profile to test the chatbot')
    parser.add_argument('--personality', required=False, help='Personality file')
    parser.add_argument("--extract", default=False, help='Path to store conversation user-chatbot')
    parser.add_argument('--verbose', action='store_true', help='Shows debug prints')
    parser.add_argument('--clean_cache', action='store_true', help='Deletes temporary files.')
    parser.add_argument('--ignore_cache', action='store_true', help='Ignores cache for temporary files')
    parser.add_argument('--update_cache', action='store_true', help='Overwrites temporary files in cache')
    args = parser.parse_args()

    logger = create_logger(args.verbose, 'Info Logger')
    logger.info('Logs enabled!')

    check_keys(["OPENAI_API_KEY"])
    generate_conversation(args.technology, args.chatbot, args.user,
                          args.personality, args.extract, args.clean_cache,
                          args.ignore_cache, args.update_cache)
