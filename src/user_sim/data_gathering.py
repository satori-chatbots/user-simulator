import os
import logging
import ast
import pandas as pd
import numpy as np
import re
from .utils.exceptions import *
from datetime import datetime
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
import json
from openai import OpenAI
client = OpenAI()


def extract_dict(in_val):
    reg_ex = r'\{[^{}]*\}'
    coincidence = re.search(reg_ex, in_val, re.DOTALL)

    if coincidence:
        return coincidence.group(0)
    else:
        return None


def to_dict(in_val):
    try:
        dictionary = ast.literal_eval(extract_dict(in_val))
    except (BadDictionaryGeneration, ValueError) as e:
        logging.getLogger().verbose(f'Bad dictionary generation for user assistant: {e}. '
                                    f'Setting empty dictionary value.')
        dictionary = {}
    return dictionary


class ChatbotAssistant:
    def __init__(self, ask_about):

        self.properties = self.process_ask_about(ask_about)
        self.system_message = {"role": "system",
                          "content": "You are a helpful assistant that detects when a query in a conversation "
                                     "has been answered or confirmed by the chatbot."}
        self.messages = [self.system_message]
        self.gathering_register = []


    @staticmethod
    def process_ask_about(ask_about):
        properties = {
        }
        for ab in ask_about:
            properties[ab.replace(' ', '_')] = {
                "type": "object",
                "properties": {
                    "verification": {
                        "type": "boolean",
                        "description": f"the following has been answered or confirmed by the chatbot: {ab}"
                    },
                    "data": {
                        "type": ["string", "null"],
                        "description": f"the piece of the conversation where the following has been answered or confirmed by the chatbot: {ab} "
                    }
                },
                "required": ["verification", "data"],
                "additionalProperties": False
            }
        return properties

    def add_message(self, history):      # add directly the chat history from user_simulator "self.conversation_history"
        text = ""
        for entry in history['interaction']:
            for speaker, message in entry.items():
                text += f"{speaker}: {message}\n"

        user_message = {"role": "user",
                        "content": text}

        self.messages = [self.system_message] + [user_message]
        self.gathering_register = self.create_dataframe()

    def get_json(self):
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=self.messages,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ask_about_validation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": self.properties,
                        "required": list(self.properties.keys()),
                        "additionalProperties": False
                    }
                }
            }
        )
        data = json.loads(response.choices[0].message.content)
        return data

    # def extract_dataframe(self, path, test_name):
    #
    #     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #     file_path = os.path.join(path, f'{test_name}_{timestamp}.csv')
    #
    #     self.gathering_register.to_csv(file_path, index=True, sep=';', header=True,
    #                                    columns=['verification', 'data'])

    def create_dataframe(self):
        data_dict = self.get_json()
        df = pd.DataFrame.from_dict(data_dict, orient='index')
        return df

    # def add_to_register(self, chatbot_msg, dictionary, user_msg):
    #
    #     df = self.gathering_register
    #
    #     ab_index = []
    #
    #     for i, question in enumerate(self.ask_about):
    #
    #         for df_index in df.index:
    #             if df.loc[df_index, 'ask_about'] == question:  # condition to update
    #                 df.loc[df_index, 'is_answered'] = dictionary[question]
    #                 if df.loc[df_index, "is_answered"]:
    #                     df.loc[df_index, "response"] = chatbot_msg
    #                     ab_index.append(i)
    #     ab_ndarray = self.ask_about
    #     ab_user_ndarray = user_msg.ask_about
    #
    #     self.ask_about = np.delete(ab_ndarray, ab_index).tolist()
    #     user_msg.ask_about = np.delete(ab_user_ndarray, ab_index).tolist()

    # @staticmethod
    # def request_control(user, chatbot):
    #     coincidence = False
    #
    #     for key in user:
    #         if user.get(key) == chatbot.get(key):
    #             coincidence = True
    #             break
    #
    #     if coincidence:
    #         return chatbot
    #     else:
    #         return {key: False for key in chatbot}

    # def response(self, chatbot_msg, user_msg):  # user_msg?? dictionary
    #
    #     chatbot_response = self.chain.run(chatbot_msg=chatbot_msg, ask_about=str(self.ask_about), user_msg=user_msg)
    #
    #     logging.getLogger().verbose(f'dictionary generated by chatbot assistant: {chatbot_response}')
    #     chatbot_response = to_dict(chatbot_response)
    #
    #     chatbot_response = self.request_control(user_msg.request, chatbot_response)
    #     self.add_to_register(chatbot_msg, chatbot_response, user_msg)
    #     return
