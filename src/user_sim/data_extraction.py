from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
import re
from dateutil import parser
import logging


class DataExtraction:

    def __init__(self, conversation, variable_name, dtype, description):

        self.conversation = conversation
        self.dtype = dtype
        self.variable = variable_name
        self.description = description
        self.prompt = """
        You're an assistant that extracts some specific information from this conversation: '{conversation}'. 
        Your output should only be the value of the data that has to be extracted, which is the following: {description}
        Please, output this data between double percentage symbol like this: %%data%%.
        {data_type}
        If you couldn't find the data, output %%None%%
        """
        self.assistant_role_prompt = PromptTemplate(
            input_variables=["conversation", "description", "data_type"],
            template=self.prompt)
        self.llm = ChatOpenAI(model="gpt-4o")
        self.chain = LLMChain(llm=self.llm, prompt=self.assistant_role_prompt)

    @staticmethod
    def regex_data(text):
        patron = re.compile(r'%%(.*?)%%')
        coincidence = patron.findall(text)
        return coincidence[0]

    @staticmethod
    def data_process(text, dtype):
        logging.getLogger().verbose(f'input text on data process for casting: {text}')
        if text == 'None':
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
            elif dtype == 'time':
                time = parser.parse(text).time().strftime("%H:%M:%S")
                return time
            elif dtype == 'date':
                date = parser.parse(text).date()
                return date
            else:
                raise ValueError(f"Unsupported data type: {dtype}")

        except ValueError as e:
            logging.getLogger().verbose(f"Error in casting: {e}")
            return None

    def get_data_prompt(self):

        data_prompts = {'int': 'Output the data as an integer',
                        'float': 'Output the data as a float',
                        'money': 'Output the data as money using the coin type in the conversation',
                        'str': "Extract and  display concisely only the requested information "
                               "without including additional context",
                        'time': 'Output the data in a "hh:mm:ss" format',
                        'date': 'Output the data in a date format understandable for Python'}

        return data_prompts.get(self.dtype)

    def get_data_extraction(self):

        llm_output = self.chain.run(conversation=self.conversation,
                                    description=self.description,
                                    data_type=self.get_data_prompt())
        logging.getLogger().verbose(f'llm output for data extraction: {llm_output}')
        text_process = self.regex_data(llm_output)
        data = self.data_process(text_process, self.dtype)

        return {self.variable: data}
