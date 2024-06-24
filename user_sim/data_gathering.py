import os
import logging
logger = logging.getLogger('mi_logger')
import ast
import pandas as pd
import numpy as np
import re

from datetime import datetime
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI



def extract_dict(input):
    reg_ex = r'\{[^{}]*\}'
    coincidence = re.search(reg_ex, input, re.DOTALL)

    if coincidence:
        return coincidence.group(0)
    else:
        return None


def to_dict(input):
    dictionary = ast.literal_eval(extract_dict(input))
    return dictionary


class user_assistant:
    def __init__(self, ask_about):
        self.prompt = """
        Assistant that detects if this sentence '{user_msg}' is asking about any of these topics: {ask_about}. 
        Answer which question is being asked in a dictionary-like way, using True or False.
        List the questions in the same order and written the same way as here {ask_about}.
        Always use the dictionary format using brackets.
        """
        self.logger = logging.getLogger('my_logger')
        self.assistant_role_prompt = PromptTemplate(
            input_variables=["user_msg", "ask_about"],
            template=self.prompt)
        self.llm = ChatOpenAI(model="gpt-4o")
        self.chain = LLMChain(llm=self.llm, prompt=self.assistant_role_prompt)
        self.ask_about = ask_about
        self.request = None

    def get_request(self, usr_msg=None):
        request_register = to_dict(self.chain.run(user_msg=usr_msg, ask_about=str(self.ask_about)))

        self.logger.info(f"user request:{request_register}")

        self.request = request_register

class chatbot_assistant:
    def __init__(self, ask_about, enable_logs=False):
        self.prompt = """
        Assistant that detects if this sentence '{chatbot_msg}' is responding to any of these questions: {ask_about}. 
        Answer which question is being answered in a dictionary-like way, using True or False.
        List the questions in the same order and written the same way as here {ask_about}.
        Always use the dictionary format using brackets.
        """
        self.logger = logging.getLogger('my_logger')
        self.assistant_role_prompt = PromptTemplate(
            input_variables=["chatbot_msg", "ask_about"],
            template=self.prompt)
        self.llm = ChatOpenAI(model="gpt-4o")
        self.chain = LLMChain(llm=self.llm, prompt=self.assistant_role_prompt)
        self.ask_about = ask_about
        self.gathering_register = self.create_dataframe(ask_about)

    def extract_dataframe(self, path, test_name):

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(path, f'{test_name}_{timestamp}.csv')

        self.gathering_register.to_csv(file_path, index=False, sep=';', header=True,
                                       columns=['ask_about', 'is_answered', 'response'])

    def create_dataframe(self, ask_about):

        df = pd.DataFrame()

        df["ask_about"] = ask_about
        df["is_answered"] = np.full(len(ask_about), fill_value=False)
        df["response"] = np.full(len(ask_about), fill_value=np.nan)
        df["response"] = df["response"].astype("object")

        return df

    def add_to_register(self, chatbot_msg, dictionary, user_msg):

        self.logger.info(f"dictionary:{dictionary}")

        df = self.gathering_register

        ab_index = []

        self.logger.info(f"'ask about' list:{self.ask_about}")
        for i, question in enumerate(self.ask_about):

            for dfindex in df.index:
                if df.loc[dfindex, 'ask_about'] == question:  # Condición para actualizar
                    df.loc[dfindex, 'is_answered'] = dictionary[question]
                    if df.loc[dfindex, "is_answered"]:
                        df.loc[dfindex, "response"] = chatbot_msg
                        ab_index.append(i)
        ab_ndarray = self.ask_about
        ab_user_ndarray = user_msg.ask_about

        self.ask_about = np.delete(ab_ndarray, ab_index).tolist()
        user_msg.ask_about = np.delete(ab_user_ndarray, ab_index).tolist()

    def request_control(self, user, chatbot):
        coincidence = False

        for key in user:
            if user.get(key) == chatbot.get(key):
                coincidence = True
                break

        if coincidence:
            return chatbot
        else:
            return {key: False for key in chatbot}

    def response(self, chatbot_msg, user_msg): #user_msg?? dictionary

        chatbot_response = self.chain.run(chatbot_msg=chatbot_msg, ask_about=str(self.ask_about))
        chatbot_response = to_dict(chatbot_response)

        self.logger.info(f"Dictionary created from chatbot response:{chatbot_response}")

        chatbot_response = self.request_control(user_msg.request, chatbot_response)
        self.add_to_register(chatbot_msg, chatbot_response, user_msg)
        return

