import ast
import pandas as pd
from .utils.token_cost_calculator import calculate_cost, max_output_tokens_allowed, max_input_tokens_allowed
import re
from .utils.exceptions import *
from .utils.utilities import parse_content_to_text
from .utils.utilities import config
import json

from openai import OpenAI
client = OpenAI()

import logging
logger = logging.getLogger('Info Logger')


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
        logger.error(f"Bad dictionary generation: {e}. Setting empty dictionary value.")
        dictionary = {}
    return dictionary


class ChatbotAssistant:
    def __init__(self, ask_about):
        self.verification_description = "the following has been answered, confirmed or provided by the chatbot:"
        self.data_description = """"the piece of the conversation where the following has been answered 
                                or confirmed by the assistant. Don't consider the user's interactions:"""
        self.properties = self.process_ask_about(ask_about)
        self.system_message = {"role": "system",
                               "content": "You are a helpful assistant that detects when a query in a conversation "
                                          "has been answered, confirmed or provided by the chatbot."}
        self.messages = [self.system_message]
        self.gathering_register = {}



    def process_ask_about(self, ask_about):
        properties = {
        }

        for ab in ask_about:
            properties[ab.replace(' ', '_')] = {
                "type": "object",
                "properties": {
                    "verification": {
                        "type": "boolean",
                        "description": f"{self.verification_description} {ab}"
                    },
                    "data": {
                        "type": ["string", "null"],
                        "description": f"{self.data_description} {ab} "
                    }
                },
                "required": ["verification", "data"],
                "additionalProperties": False
            }
        return properties

    def add_message(self, history):     # adds directly the chat history from user_simulator "self.conversation_history"
        text = ""
        for entry in history['interaction']:
            for speaker, message in entry.items():
                text += f"{speaker}: {message}\n"

        user_message = {"role": "user",
                        "content": text}

        self.messages = [self.system_message] + [user_message]
        self.gathering_register = self.create_dataframe()


    def get_json(self):
        model = "gpt-4o-mini"
        params = {
            "model": model,
            "messages": self.messages,
            "response_format":{
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
        }
        if config.token_count_enabled:
            params["max_completion_tokens"] = max_output_tokens_allowed(model)


        parsed_input_message = parse_content_to_text(
            self.messages) + self.verification_description + self.data_description

        if max_input_tokens_allowed(parsed_input_message, model):
            logger.error(f"Token limit was surpassed")
            return None

        response = client.chat.completions.create(**params)
        output_message = response.choices[0].message.content

        try:
            data = json.loads(output_message)
        except Exception as e:
            logger.error(f"Truncated data in message: {output_message}")
            data = None
        calculate_cost(parsed_input_message, output_message, model=model, module="data_gathering")
        return data

    def create_dataframe(self):
        data_dict = self.get_json()
        if data_dict is None:
            df = self.gathering_register
        else:
            df = pd.DataFrame.from_dict(data_dict, orient='index')
        return df

