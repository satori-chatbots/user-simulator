import json
import uuid
from abc import abstractmethod
import requests
from user_sim.utils.config import errors
import logging
logger = logging.getLogger('Info Logger')

###################################################
# THE CONNECTORS NEED HEAVY REFACTORING TO JUST
# ONE OR TWO CLASSES

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

##############################################################################################################
# Serviceform
class ChatbotServiceform(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.url = "https://dash.serviceform.com/api/ai"
        self.headers = {
            'Content-Type': 'text/plain;charset=UTF-8'
        }
        self.payload = {"sid":"1729589460223tvzbcxe5zocgr5hs",
                        "tid":"haGDRXUPY9tQOsOS44jY",
                        "message":"Hello",
                        "extraTraining":"",
                        "assistant_id":"asst_PUNPPDAFOgHRLrlmHhDuQhCM"}

    def execute_with_input(self, user_msg):
        self.payload['message'] = user_msg
        timeout = 10000
        try:
            response = requests.post(self.url, headers=self.headers, json=self.payload, timeout=timeout)
            if response.status_code == 200:
                data_bytes = response.content
                data_str = data_bytes.decode('utf-8')
                data_dict = json.loads(data_str)
                return True, data_dict['response']
            else:
                # There is an error, but it is an internal error
                print(f"Server error {response.status_code}")
                errors.append({response.status_code: f"Couldn't get response from the server"})
                return False, f"Something went wrong. Status Code: {response.status_code}"
        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('my_app_logger')
            logger.log(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'
        except requests.Timeout:
            logger = logging.getLogger('my_app_logger')
            logger.error(f"No response was received from the server in less than {timeout}")
            errors.append({504: f"No response was received from the server in less than {timeout}"})
            return False, 'timeout'



##############################################################################################################
# Kuki chatbot
class KukiChatbot(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)
        self.url = "https://kuli.kuki.ai/cptalk"
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded'  # Standard for form data
        }
        self.payload = {
            'uid': '54d5a563617d1999',
            'input': 'And before?',
            'sessionid': '485198820'
        }

    def execute_with_input(self, user_msg):
        self.payload['input'] = user_msg
        timeout = 10000
        try:
            response = requests.post(self.url, headers=self.headers, data=self.payload, timeout=timeout)
            if response.status_code == 200:
                response_dict = json.loads(response.text)
                responses = response_dict['responses']
                all_responses = '\n'.join(responses)
                return True, all_responses
            else:
                # There is an error, but it is an internal error
                print(f"Server error {response.status_code}")
                errors.append({response.status_code: f"Couldn't get response from the server"})
                return False, f"Something went wrong. Status Code: {response.status_code}"
        except requests.exceptions.JSONDecodeError as e:
            logger = logging.getLogger('my_app_logger')
            logger.log(f"Couldn't get response from the server: {e}")
            return False, 'chatbot internal error'
        except requests.Timeout:
            logger = logging.getLogger('my_app_logger')
            logger.error(f"No response was received from the server in less than {timeout}")
            errors.append({504: f"No response was received from the server in less than {timeout}"})
            return False, 'timeout'



class SprinklChatbot(Chatbot):
    def __init__(self, url):
        Chatbot.__init__(self, url)

        self.headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    #"Content-Length": "2474",
    "Content-Type": "application/x-www-form-urlencoded",
    #"Host": "prod2-live-chat-champagne.sprinklr.com",
    "Origin": "null",
    "Priority": "u=0, i",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "TE": "trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"
}

        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',  # Standard for form data
        }

        self.url = "https://prod2-live-chat-champagne.sprinklr.com/api/livechat"
        self.conversation = None

    def execute_with_input(self, user_msg):
        import urllib.parse

        if self.conversation is None:
            try:
                payload = {"p": {"createCase": False,
                           "startedByContext":{},
                           "pageTitle":"Sprinklr: Unified AI-Powered Customer Experience Management Platform",
                           "pageUrl":"https://www.sprinklr.com/",
                           "userAgent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
                           "timeZone":"Europe/Madrid","locale":"en"},
                           }

                #payload['p'] = {"conversationId":"6718124d09a1f6285cb9f6e0",
                #                "messagePayload":{"text":"hi","textEntities":[],"messageType":313,"disableManualResponse":False},"sender":"A_671808ee09a1f6285cb6a85d","clientMessageId":"2c4b39b5-cbf6-4ee5-a3bd-ba85279f1b30","inReplyToChatMessageId":"6718124d09a1f6285cb9f6e1"}

                payload = 	{
"p":	{"createCase":False,
         "startedByContext":{},
         "pageTitle":"Sprinklr: Plataforma unificada de gestión de la experiencia del cliente basada en IA",
         "pageUrl":"https://www.sprinklr.com/es/",
         "userAgent":"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
         "timeZone":"Europe/Madrid","locale":"en"}
,
"x-chat-referer":	"https://www.sprinklr.com/es/",
"x-chat-origin":	"https://www.sprinklr.com",
"x-chat-page-title":	"Sprinklr: Plataforma unificada de gestión de la experiencia del cliente basada en IA",
"x-chat-version":	"WgRhbCFIj",
"x-chat-sdk":	"Web",
"x-chat-token":	"eyJhbGciOiJSUzI1NiJ9.eyJ2aXNpdFNlc3Npb25JZCI6IjY3MTk2MzYzYjllNjRmNWNjNzAyYWFmZSIsInN1YiI6IkFjY2VzcyBUb2tlbiBHZW5lcmF0ZWQgQnkgU3ByaW5rbHIiLCJjaGF0TG9jYWxlIjoiZW4iLCJjaGF0VXNlckhhc0NvbnZlcnNhdGlvblN0YXJ0ZWQiOmZhbHNlLCJpc3MiOiJTUFJJTktMUiIsInZpc2l0U2Vzc2lvbklkRXhwaXJlQXQiOjE3Mjk3NjAyOTExNjUsInR5cCI6IkpXVCIsImlzRGVmbGVjdGlvblRva2VuIjpmYWxzZSwidXNlclNlc3Npb25Mb2dpbk1ldGhvZCI6IntcInR5cGVcIjpcIkFOT05ZTU9VU1wifSIsImNoYXRVc2VySWQiOiJBXzY3MTgwOGVlMDlhMWY2Mjg1Y2I2YTg1ZCIsImFwcElkIjoiYXBwXzEwMDQzODM0NSIsInNjb3BlIjpbIl…wOWExZjYyODVjYjZhODVkXCIsXCJpbmJveC9BXzY3MTgwOGVlMDlhMWY2Mjg1Y2I2YTg1ZFwiXX0iLCJjaGF0VXNlclR5cGUiOiJBTk9OWU1PVVMiLCJwYXJ0bmVySWQiOjUwNDAwLCJ0b2tlblR5cGUiOiJBQ0NFU1MifQ.b92sN2b_DpY3d8lpJTuDmS3-DJqX2fzg7RsZ6Es1NKXBFUOeimATEq1iL-wf8GSAv8E1Pzw4IKcAHisBQk8pUMwgWChyd5sqnPxgQ348lcVHqYn9SmW7YOA_yn4jSmrbe-xjORmXbU6IvH7oJUvyGYeSrWn6RR5q7eBu72OYVDn5AziEb8a-jYMmGMarctznXtF7Et9Y_YA8dOmJhh8Ndch9_O5yuosoSJvt6_wyLq438QftLWUvzFKgUt9oec-7ccEyLysmsdCj-BajxomW9K4XT40ktXalE1JK3t3Jmp4lNHqb_zZRhdfqIJIRcVO42N381gXOOownM0UtxtPuYw",
"x-user-id":	"A_671808ee09a1f6285cb6a85d",
"x-client-id":	"1552a9b4-50fc-4fa5-bb97-8002c682b102_1_1",
"x-chat-appId":	"62fe5a7833099a5ea6705eb6_app_100438345"
                }

                # Serialize payload as json string
                payload['p'] = json.dumps(payload['p'], separators=(',', ':'))
                print("==> ", payload['p'])
                print("==> ", urllib.parse.urlencode({"p": payload['p']}))

                payload = urllib.parse.urlencode(payload)
                payload_ok = "p=%7B%22createCase%22%3Afalse%2C%22startedByContext%22%3A%7B%7D%2C%22pageTitle%22%3A%22Sprinklr%3A%20Plataforma%20unificada%20de%20gesti%C3%B3n%20de%20la%20experiencia%20del%20cliente%20basada%20en%20IA%22%2C%22pageUrl%22%3A%22https%3A%2F%2Fwww.sprinklr.com%2Fes%2F%22%2C%22userAgent%22%3A%22Mozilla%2F5.0%20(X11%3B%20Ubuntu%3B%20Linux%20x86_64%3B%20rv%3A131.0)%20Gecko%2F20100101%20Firefox%2F131.0%22%2C%22timeZone%22%3A%22Europe%2FMadrid%22%2C%22locale%22%3A%22en%22%7D&x-chat-referer=https%3A%2F%2Fwww.sprinklr.com%2Fes%2F&x-chat-origin=https%3A%2F%2Fwww.sprinklr.com&x-chat-page-title=Sprinklr%3A%20Plataforma%20unificada%20de%20gesti%C3%B3n%20de%20la%20experiencia%20del%20cliente%20basada%20en%20IA&x-chat-version=WgRhbCFIj&x-chat-sdk=Web&x-chat-token=eyJhbGciOiJSUzI1NiJ9.eyJ2aXNpdFNlc3Npb25JZCI6IjY3MTk2MzYzYjllNjRmNWNjNzAyYWFmZSIsInN1YiI6IkFjY2VzcyBUb2tlbiBHZW5lcmF0ZWQgQnkgU3ByaW5rbHIiLCJjaGF0TG9jYWxlIjoiZW4iLCJjaGF0VXNlckhhc0NvbnZlcnNhdGlvblN0YXJ0ZWQiOmZhbHNlLCJpc3MiOiJTUFJJTktMUiIsInZpc2l0U2Vzc2lvbklkRXhwaXJlQXQiOjE3Mjk3NjAyOTExNjUsInR5cCI6IkpXVCIsImlzRGVmbGVjdGlvblRva2VuIjpmYWxzZSwidXNlclNlc3Npb25Mb2dpbk1ldGhvZCI6IntcInR5cGVcIjpcIkFOT05ZTU9VU1wifSIsImNoYXRVc2VySWQiOiJBXzY3MTgwOGVlMDlhMWY2Mjg1Y2I2YTg1ZCIsImFwcElkIjoiYXBwXzEwMDQzODM0NSIsInNjb3BlIjpbIlJFQUQiLCJXUklURSJdLCJleHAiOjE3Mjk3NjAyOTEsImF1dGhUeXBlIjoiU1BSX0tFWV9QQVNTX0xPR0lOIiwiaWF0IjoxNzI5NzE3MDkxLCJqdGkiOiJjYWY5ZDJmYS00OTVlLTQ5ZTMtOWE3Ny1hMjQzMTNmZDU1OTAiLCJhbm9ueW1vdXNJZCI6IkFfNjcxODA4ZWUwOWExZjYyODVjYjZhODVkIiwiY2xpZW50SWQiOjMxMDUsInN0cmljdFVzZXJBdXRoZW50aWNhdGlvbiI6ZmFsc2UsInVzZXJJZCI6MCwiYXVkIjoiU1BSSU5LTFIiLCJuYmYiOjE3Mjk3MTU4OTEsInZpc2l0U2Vzc2lvblN0YXJ0VGltZSI6MTcyOTcxNzA5MTE1NSwibXF0dEFjbCI6IntcInBcIjpbXCJwdWJsaXNoL0FfNjcxODA4ZWUwOWExZjYyODVjYjZhODVkL3B0ci01MDQwMC10b3BpY1wiXSxcInNcIjpbXCJhcHBfMTAwNDM4MzQ1X2luYm94L0FfNjcxODA4ZWUwOWExZjYyODVjYjZhODVkXCIsXCJpbmJveC9BXzY3MTgwOGVlMDlhMWY2Mjg1Y2I2YTg1ZFwiXX0iLCJjaGF0VXNlclR5cGUiOiJBTk9OWU1PVVMiLCJwYXJ0bmVySWQiOjUwNDAwLCJ0b2tlblR5cGUiOiJBQ0NFU1MifQ.b92sN2b_DpY3d8lpJTuDmS3-DJqX2fzg7RsZ6Es1NKXBFUOeimATEq1iL-wf8GSAv8E1Pzw4IKcAHisBQk8pUMwgWChyd5sqnPxgQ348lcVHqYn9SmW7YOA_yn4jSmrbe-xjORmXbU6IvH7oJUvyGYeSrWn6RR5q7eBu72OYVDn5AziEb8a-jYMmGMarctznXtF7Et9Y_YA8dOmJhh8Ndch9_O5yuosoSJvt6_wyLq438QftLWUvzFKgUt9oec-7ccEyLysmsdCj-BajxomW9K4XT40ktXalE1JK3t3Jmp4lNHqb_zZRhdfqIJIRcVO42N381gXOOownM0UtxtPuYw&x-user-id=A_671808ee09a1f6285cb6a85d&x-client-id=1552a9b4-50fc-4fa5-bb97-8002c682b102_1_1&x-chat-appId=62fe5a7833099a5ea6705eb6_app_100438345"
                payload_ko = "p=%7B%22createCase%22%3Afalse%2C%22startedByContext%22%3A%7B%7D%2C%22pageTitle%22%3A%22Sprinklr%3A+Plataforma+unificada+de+gesti%C3%B3n+de+la+experiencia+del+cliente+basada+en+IA%22%2C%22pageUrl%22%3A%22https%3A%2F%2Fwww.sprinklr.com%2Fes%2F%22%2C%22userAgent%22%3A%22Mozilla%2F5.0+%28X11%3B+Ubuntu%3B+Linux+x86_64%3B+rv%3A131.0%29+Gecko%2F20100101+Firefox%2F131.0%22%2C%22timeZone%22%3A%22Europe%2FMadrid%22%2C%22locale%22%3A%22en%22%7D&x-chat-referer=https%3A%2F%2Fwww.sprinklr.com%2Fes%2F&x-chat-origin=https%3A%2F%2Fwww.sprinklr.com&x-chat-page-title=Sprinklr%3A+Plataforma+unificada+de+gesti%C3%B3n+de+la+experiencia+del+cliente+basada+en+IA&x-chat-version=WgRhbCFIj&x-chat-sdk=Web&x-chat-token=eyJhbGciOiJSUzI1NiJ9.eyJ2aXNpdFNlc3Npb25JZCI6IjY3MTk2MzYzYjllNjRmNWNjNzAyYWFmZSIsInN1YiI6IkFjY2VzcyBUb2tlbiBHZW5lcmF0ZWQgQnkgU3ByaW5rbHIiLCJjaGF0TG9jYWxlIjoiZW4iLCJjaGF0VXNlckhhc0NvbnZlcnNhdGlvblN0YXJ0ZWQiOmZhbHNlLCJpc3MiOiJTUFJJTktMUiIsInZpc2l0U2Vzc2lvbklkRXhwaXJlQXQiOjE3Mjk3NjAyOTExNjUsInR5cCI6IkpXVCIsImlzRGVmbGVjdGlvblRva2VuIjpmYWxzZSwidXNlclNlc3Npb25Mb2dpbk1ldGhvZCI6IntcInR5cGVcIjpcIkFOT05ZTU9VU1wifSIsImNoYXRVc2VySWQiOiJBXzY3MTgwOGVlMDlhMWY2Mjg1Y2I2YTg1ZCIsImFwcElkIjoiYXBwXzEwMDQzODM0NSIsInNjb3BlIjpbIl%E2%80%A6wOWExZjYyODVjYjZhODVkXCIsXCJpbmJveC9BXzY3MTgwOGVlMDlhMWY2Mjg1Y2I2YTg1ZFwiXX0iLCJjaGF0VXNlclR5cGUiOiJBTk9OWU1PVVMiLCJwYXJ0bmVySWQiOjUwNDAwLCJ0b2tlblR5cGUiOiJBQ0NFU1MifQ.b92sN2b_DpY3d8lpJTuDmS3-DJqX2fzg7RsZ6Es1NKXBFUOeimATEq1iL-wf8GSAv8E1Pzw4IKcAHisBQk8pUMwgWChyd5sqnPxgQ348lcVHqYn9SmW7YOA_yn4jSmrbe-xjORmXbU6IvH7oJUvyGYeSrWn6RR5q7eBu72OYVDn5AziEb8a-jYMmGMarctznXtF7Et9Y_YA8dOmJhh8Ndch9_O5yuosoSJvt6_wyLq438QftLWUvzFKgUt9oec-7ccEyLysmsdCj-BajxomW9K4XT40ktXalE1JK3t3Jmp4lNHqb_zZRhdfqIJIRcVO42N381gXOOownM0UtxtPuYw&x-user-id=A_671808ee09a1f6285cb6a85d&x-client-id=1552a9b4-50fc-4fa5-bb97-8002c682b102_1_1&x-chat-appId=62fe5a7833099a5ea6705eb6_app_100438345"

                payload = payload.replace("+", "%20")

                print(payload_ok)
                print("-----------------")
                print(payload)
                print(payload_ok == payload)
                # , timeout=timeout
                "/api/livechat/conversation/send"

                #payload = payload_ko


                post_response = requests.post("https://prod2-live-chat-champagne.sprinklr.com/api/livechat/conversation/new",
                                              data=payload, headers=self.headers)
                #post_response = requests.post(self.url + '/conversation/send', data=payload, headers=self.headers)

                # 'https://prod2-live-chat-champagne.sprinklr.com/api/livechat/conversation/new'
                post_response_json = post_response.json()
                print(post_response_json)
                #self.conversation = post_response_json.get('id')
            except requests.exceptions.ConnectionError:
                logger.error(f"Couldn't connect with chatbot")
                errors.append({500: f"Couldn't connect with chatbot"})
                return False, 'cut connection'

        # https://prod2-live-chat-champagne.sprinklr.com/api/livechat/conversation/new

        #{"conversationId": "6718124d09a1f6285cb9f6e0",
        # "messagePayload": {"text": "hi", "textEntities": [], "messageType": 313, "disableManualResponse": false},
        # "sender": "A_671808ee09a1f6285cb6a85d", "clientMessageId": "2c4b39b5-cbf6-4ee5-a3bd-ba85279f1b30",
        # "inReplyToChatMessageId": "6718124d09a1f6285cb9f6e1"}

SprinklChatbot(None).execute_with_input("Hola")