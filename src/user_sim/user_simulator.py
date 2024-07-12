import openai
from utils.show_logs import LoggerConfig
from utils.utilities import *
from data_gathering import *

from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI


def generar_interaccion(msg, temperatura=0.8, max_tokens=300):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=msg,
        temperature=temperatura,
        max_tokens=max_tokens
    )
    return response['choices'][0]['message']['content'].strip()


class user_generation:

    def __init__(self, user_profile, chatbot, enable_logs=True):

        self.user_profile = user_profile
        self.chatbot = chatbot
        self.logger_config = LoggerConfig(mostrar_logs=enable_logs)
        self.logger = logging.getLogger('my_logger')  #???
        self.temp = user_profile.temperature
        self.user_llm = ChatOpenAI(model="gpt-4o", temperature=self.temp)
        self.conversation_history = {'interaction': []}
        # self.ask_about = list_to_phrase(user_profile.ask_about, prompted=True)
        self.ask_about = user_profile.ask_about.prompt()
        self.request_register = user_assistant(user_profile.ask_about.phrases)
        self.data_gathering = chatbot_assistant(user_profile.ask_about.phrases)
        self.user_role_prompt = PromptTemplate(
            input_variables=["reminder", "history"],
            template=self.set_role_template()
        )

        self.test_name = user_profile.test_name
        self.repeat_count = 0
        self.loop_count = 0
        self.interaction_count = 0
        self.user_chain = LLMChain(llm=self.user_llm, prompt=self.user_role_prompt)
        self.my_context = self.initial_context()

    class initial_context:
        def __init__(self):
            self.original_context = []
            self.context_list = []

        def initiate_context(self, context):

            default_context = ["never indicate that you are the user, like 'user: bla bla'",
                               'Sometimes, interact with what the assistant just said.',
                               'Never act as the assistant, always behave as a user.',
                               "Don't end the conversation until you've asked everything you need."]

            if isinstance(context, list):
                self.original_context = context.copy() + default_context.copy()
                self.context_list = context.copy() + default_context.copy()
            else:
                self.original_context = [context] + default_context
                self.context_list = [context] + default_context
                # self.original_context.append(context)
                # self.context_list.append(context)

        def add_context(self, new_context):
            if isinstance(new_context, list):
                for cont in new_context:
                    self.context_list.append(cont)
            else:
                self.context_list.append(new_context)  #TODO: add exception to force the user to initiate the context


        def get_context(self):
            return '. '.join(self.context_list)

        def reset_context(self):
            self.context_list = self.original_context.copy()

    def set_role_template(self):
        reminder = """{reminder}"""
        history = """History of the conversation so far: {history}"""
        role_prompt = self.user_profile.role + reminder + history
        return role_prompt

    def add_register(self, msg: list[dict]):
        self.conv_register = self.conv_register + msg

    def save_data_gathering(self, path):
        self.data_gathering.extract_dataframe(path, self.test_name)

    def get_info(self):
        info = {"context": self.context,
                "register": self.conv_register,
                "user_profile": self.user_act,
                "language": self.language,
                "keep_context": self.keep_context,
                "ask_about": self.ask_about,
                "temperature": self.temp}
        return info

    def repetition_track(self, response, reps=3):

        self.my_context.reset_context()
        print(self.my_context.context_list)
        if nlp_processor(response, self.chatbot.fallback, 0.6):
            self.repeat_count += 1
            self.loop_count += 1
            self.logger.info("is end")

            if self.repeat_count >= reps:
                self.repeat_count = 0
                change_topic = """
                               Since the assistant is not understanding what you're saying, change the 
                               topic to other things to ask about without starting a new conversation
                               """

                self.my_context.add_context(change_topic)

            else:
                ask_repetition = """
                                If the assistant asks you to repeat the question, repeat the last question the user 
                                said but rephrase it.
                                """

                self.my_context.add_context(ask_repetition)
        else:
            self.repeat_count = 0
            self.loop_count = 0


    @staticmethod
    def conversation_ending(response):
        return nlp_processor(response, "src/testing/user_sim/end_conversation_patterns.yml", 0.5)

    def get_history(self):

        lines = []
        for inp in self.conversation_history['interaction']:
            for k, v in inp.items():
                lines.append(f"{k}: {v}")
        return "\n".join(lines)

    def update_history(self, role, message):
        self.conversation_history['interaction'].append({role: message})


    def end_conversation(self, input_msg):

        if self.user_profile.goal_style[0] == 'steps' or self.user_profile.goal_style[0] == 'random steps':
            if self.interaction_count >= self.user_profile.goal_style[1]:
                self.logger.info("is end")
                return True

        elif self.conversation_ending(input_msg) or self.loop_count >= 9:
            self.logger.info("is end")
            return True

        elif (self.data_gathering.gathering_register["is_answered"].all()
              and (self.user_profile.goal_style[0] == 'all answered' or self.user_profile.goal_style[0] == 'default')):
            self.logger.info("is end")
            return True

        else:
            return False

    def get_response(self, input_msg):

        self.data_gathering.response(input_msg, self.request_register)

        self.update_history("Assistant", input_msg)

        if self.end_conversation(input_msg):
            return "exit"

        self.repetition_track(input_msg)

        self.my_context.add_context(self.user_profile.get_language())

        history = self.get_history()

        # Generar la respuesta del usuario
        user_response = self.user_chain.run(history=history,
                                            reminder=self.my_context.get_context())

        # self.my_context.reset_context()
        self.request_register.get_request(user_response)

        self.update_history("User", user_response)

        self.interaction_count += 1

        return user_response

    @staticmethod
    def formatting(role, msg):
        return [{"role": role, "content": msg}]
    def get_interaction_styles_prompt(self):
        interaction_style_prompt = []
        for instance in self.user_profile.interaction_styles:
            if instance.change_language_flag:
                pass
            else:
                interaction_style_prompt.append(instance.get_prompt())
        return ''.join(interaction_style_prompt)

    def open_conversation(self):
        # print(type(self.user_profile.language))

        interaction_style_prompt = self.get_interaction_styles_prompt()
        self.my_context.initiate_context([self.user_profile.context,
                                          interaction_style_prompt,
                                          self.ask_about])

        language_context = self.user_profile.get_language()
        self.my_context.add_context(language_context)
        history = self.get_history()
        user_response = self.user_chain.run(history=history,
                                            reminder=self.my_context.get_context())  # generation of user message

        self.update_history("User", user_response)

        self.request_register.get_request(user_response)
        self.interaction_count += 1
        return user_response
