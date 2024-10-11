import logging
import uuid
from abc import abstractmethod
import requests

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
            return True, post_response_json[0].get('text')
        else:
            return True, ''


##############################################################################################################
# ADA-UAM
class ChatbotAdaUam(Chatbot):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'API-KEY 60a3bee2e3987316fed3218f'
    }

    payload = {"conversation": "670577afe0d59bbc894897b2",
               "sender_type": "User", "sender": "670577af4e61b2bc9462703f",
               "bot": "60a3be81f9a6b98f7659a6f9", "language": "es",
               "url": "https://www.uam.es/uam/tecnologias-informacion",
               "message": { "text" : "Hola"}}

    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.id = None
        self.url = "https://api.1millionbot.com/api/public/messages"


    def execute_with_input(self, user_msg):
        self.payload['message']["text"] = user_msg
        try:
            response = requests.post(self.url, headers=self.headers, json=self.payload)
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
                                    for button in card['buttons']:
                                        if 'text' in button:
                                            text_response += f"- BUTTON TEXT: {button['text']}"
                                        if 'value' in button:
                                            text_response += f" LINK: {button['value']}\n"
                return True, text_response
            else:
                # There is an error, but it is an internal error
                print (f"Server error {response_json.get('error')}")
                return False, response_json.get('error')
        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('my_app_logger')
            logger.log(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'


##############################################################################################################
# Taskyto
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
                if post_response.status_code == 200:
                    return True, post_response_json.get('message')
                else:
                    # There is an error, but it is an internal error
                    return False, post_response_json.get('error')
            except requests.exceptions.JSONDecodeError as e:
                logger = logging.getLogger('my_app_logger')
                logger.log(f"Couldn't get response from the server: {e}")
                return False, 'chatbot internal error'

        return True, ''