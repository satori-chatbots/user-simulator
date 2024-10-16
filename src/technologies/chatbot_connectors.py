import uuid
from abc import abstractmethod
import requests
from user_sim.utils.config import errors
import logging
logger = logging.getLogger('Info Logger')
class Chatbot:
    def __init__(self, url):
        self.url = url
        self.fallback = 'I do not understand you'

    @abstractmethod
    def execute_with_input(self, user_msg):
        """Returns a pair [bool, str] in which the first element is True if the chatbot returned normally,
           and the second is the message.
           Otherwise, False means that there is an error in the chatbot."""
        raise NotImplementedError()


##############################################################################################################
# RASA
class ChatbotRasa(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.id = None

    def execute_with_input(self, user_msg):
        if self.id is None:
            self.id = str(uuid.uuid4())

        new_data = {
            "sender": self.id,
            "message": user_msg
        }
        post_response = requests.post(self.url, json=new_data)
        post_response_json = post_response.json()
        if len(post_response_json) > 0:
            message = '\n'.join([r.get('text') for r in post_response_json])
            return True, message
        else:
            return True, ''


##############################################################################################################
# 1million bot chatbots
class MillionBot(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.headers = {}
        self.payload = {}
        self.id = None

    def execute_with_input(self, user_msg):
        self.payload['message']["text"] = user_msg
        timeout = 10
        try:
            response = requests.post(self.url, headers=self.headers, json=self.payload, timeout=timeout)
            response_json = response.json()
            if response.status_code == 200:
                text_response = ""
                for answer in response_json['response']:
                    # to-do --> pass the buttons in the answer?
                    if 'text' in answer:
                        text_response += answer['text']+"\n"
                    elif 'payload' in answer:
                        text_response += f"\n\nAVAILABLE BUTTONS:\n\n"
                        if 'cards' in answer['payload']:
                            for card in answer['payload']['cards']:
                                if 'buttons' in card:
                                    text_response += self.__translate_buttons(card['buttons'])
                        elif 'buttons' in answer['payload']:
                            text_response += self.__translate_buttons(answer['payload']['buttons'])

                return True, text_response
            else:
                # There is an error, but it is an internal error
                print (f"Server error {response_json.get('error')}")
                errors.append({500: f"Couldn't get response from the server"})
                return False, response_json.get('error')
        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('my_app_logger')
            logger.log(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'
        except requests.Timeout:
            logger = logging.getLogger('my_app_logger')
            logger.error(f"No response was received from the server in less than {timeout}")
            errors.append({504: f"No response was received from the server in less than {timeout}"})
            return False, 'timeout'

    def __translate_buttons(self, buttons_list) -> str:
        text_response = ''
        for button in buttons_list:
            if 'text' in button:
                text_response += f"- BUTTON TEXT: {button['text']}"
            if 'value' in button:
                text_response += f" LINK: {button['value']}\n"
            else:
                text_response += f" LINK: <empty>\n"
        return text_response


##############################################################################################################
# ADA-UAM
class ChatbotAdaUam(MillionBot):
    def __init__(self, url):
        MillionBot.__init__(self, url)
        self.id = None
        self.url = "https://api.1millionbot.com/api/public/messages"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'API-KEY 60a3bee2e3987316fed3218f'
        }

        self.payload = {"conversation": "670577afe0d59bbc894897b2",
                   "sender_type": "User", "sender": "670577af4e61b2bc9462703f",
                   "bot": "60a3be81f9a6b98f7659a6f9", "language": "es",
                   "url": "https://www.uam.es/uam/tecnologias-informacion",
                   "message": {"text": "Hola"}}


class ChatbotMillionBot(MillionBot):
    def __init__(self, url):
        MillionBot.__init__(self, url)
        self.id = None
        self.url = "https://api.1millionbot.com/api/public/messages"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'API-KEY 6465e8319de7b94a9cf0138a'
        }

        self.payload = {"conversation":"670cf272ddbe1af483229440",
                        "sender_type":"User",
                        "sender":"670cf2727516491d1c6f69a5",
                        "bot":"6465e8319de7b94a9cf01387",
                        "language":"es",
                        "url":"https://1millionbot.com/",
                        "message":{"text":"Hola, ¿qué es un chatbot?"}}

class ChatbotLolaUMU(MillionBot):
    def __init__(self, url):
        MillionBot.__init__(self, url)
        self.id = None
        self.url = "https://api.1millionbot.com/api/public/messages"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'API-KEY 60553d58c41f5dfa095b34b5'
        }

        self.payload = {"conversation":"670d14d95771b0aa274c97fa",
                        "sender_type":"User",
                        "sender":"670d14d97516491d1c7109c1",
                        "bot":"5af00c50f9639920a0e4769b",
                        "language":"es",
                        "url":"https://www.um.es/web/estudios/acceso/estudiantes-bachillerato-y-ciclos-formativos",
                        "message":{"text":"Hola"}}

##############################################################################################################
# Taskyto
class ChatbotTaskyto(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.id = None

    def execute_with_input(self, user_msg):
        if self.id is None:
            try:
                post_response = requests.post(self.url + '/conversation/new')
                post_response_json = post_response.json()
                self.id = post_response_json.get('id')
            except requests.exceptions.ConnectionError:
                logger.error(f"Couldn't connect with chatbot")
                errors.append({500: f"Couldn't connect with chatbot"})
                return False, 'cut connection'

        if self.id is not None:
            new_data = {
                "id": self.id,
                "message": user_msg
            }

            try:
                timeout = 10
                try:
                    post_response = requests.post(self.url + '/conversation/user_message', json=new_data, timeout=timeout)
                except requests.Timeout:
                    logger.error(f"No response was received from the server in less than {timeout}")
                    errors.append({504: f"No response was received from the server in less than {timeout}"})
                    return False, 'timeout'
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"Couldn't get response from the server: {e}")
                    errors.append({500: f"Couldn't get response from the server"})
                    return False, 'chatbot internal error'

                post_response_json = post_response.json()

                if post_response.status_code == 200:
                    assistant_message = post_response_json.get('message')
                    return True, assistant_message

                else:
                    # There is an error, but it is an internal error
                    errors.append({500: "Chatbot internal error"})
                    return False, post_response_json.get('error')
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"Couldn't get response from the server: {e}")
                errors.append({500: f"Couldn't get response from the server"})
                return False, 'chatbot internal error'

        return True, ''