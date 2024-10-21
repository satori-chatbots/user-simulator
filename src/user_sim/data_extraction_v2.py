import re
import logging
import json
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from openai import OpenAI
from dateutil import parser

client = OpenAI()
logger = logging.getLogger('Info Logger')


class DataExtraction:

    def __init__(self, conversation, variable_name, dtype, description):

        self.conversation = f"{conversation['interaction']}"
        self.dtype = dtype
        self.variable = variable_name
        self.description = description
        self.prompt = f"""
        You're an assistant that extracts some specific information from a conversation.
        """
        # Please, output
        # this
        # data
        # between
        # double
        # percentage
        # symbol
        # like
        # this: %%data %%.
        # {data_type}
        self.system_message = [
            {"role": "system",
             "content": self.prompt},
            {"role": "user",
             "content": self.conversation}
        ]
        # self.assistant_role_prompt = PromptTemplate(
        #     input_variables=["conversation", "description", "data_type"],
        #     template=self.prompt)
        # self.llm = ChatOpenAI(model="gpt-4o")
        # self.chain = self.assistant_role_prompt | self.llm

    @staticmethod
    def regex_data(text):
        patron = re.compile(r'%%(.*?)%%')
        coincidence = patron.findall(text)
        if coincidence[0] == 'None':
            return None
        else:
            return coincidence[0]

    @staticmethod
    def data_process(text, dtype):
        logger.info(f'input text on data process for casting: {text}')
        if text is None or text == 'null':
            return text
        try:
            if dtype == 'int':
                return int(text)
            elif dtype == 'float':
                return float(text)
            elif dtype == 'money':
                return text
            elif dtype == 'str':
                return str(text)
            elif dtype == 'bool':
                return bool(text)
            elif dtype == 'time':
                time = parser.parse(text).time().strftime("%H:%M:%S")
                return time
            elif dtype == 'date':
                date = parser.parse(text).date()
                return date
            else:
                return text
                #raise ValueError(f"Unsupported data type: {dtype}")

        except ValueError as e:
            logger.warning(f"Error in casting: {e}. Returning 'str({str(text)})'.")
            return str(text)

    # def get_data_prompt(self):
    #
    #     data_prompts = {'int': 'Output the data as an integer',
    #                     'float': 'Output the data as a float',
    #                     'money': 'Output the data as money with the currency used in the conversation',
    #                     'str': "Extract and  display concisely only the requested information "
    #                            "without including additional context",
    #                     'time': 'Output the data in a "hh:mm:ss" format',
    #                     'date': 'Output the data in a date format understandable for Python'}
    #
    #     return data_prompts.get(self.dtype)

    def get_data_prompt(self):

        data_type = {'int': 'integer',
                        'float': 'number',
                        'money': 'string',
                        'str': "string",
                        'time': 'string',
                        'bool': 'boolean',
                        'date': 'string'}
        data_format = {'int': '',
                        'float': '',
                        'money': 'Output the data as money with the currency used in the conversation',
                        'str': "Extract and  display concisely only the requested information "
                               "without including additional context",
                        'time': 'Output the data in a "hh:mm:ss" format',
                        'date': 'Output the data in a date format understandable for Python'}

        type = data_type.get(self.dtype)
        d_format = data_format.get(self.dtype)
        return type, d_format

    def get_data_extraction(self):

        dtype = self.get_data_prompt()[0]
        format = self.get_data_prompt()[1]
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "data_extraction",
                "strict": True,
                "schema": {
                    "type": "object",
                    "required": ["answer"],
                    "additionalProperties": False,
                    "properties": {
                        "answer": {
                            "type": [dtype, 'null'],
                            "description": f"{self.description}. {format}"
                        }
                    }
                }
            }
        }

        # llm_output = self.chain.invoke({'conversation': self.conversation,
        #                                 'description': self.description,
        #                                 'data_type': self.get_data_prompt()})

        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=self.system_message,
            response_format=response_format
        )
        llm_output = json.loads(response.choices[0].message.content)

        logger.info(f'LLM output for data extraction: {llm_output}')
        # text_process = self.regex_data(llm_output.content)
        data = self.data_process(llm_output, self.dtype)
        return {self.variable: data}
