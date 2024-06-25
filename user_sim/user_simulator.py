import openai
from user_sim.show_logs import LoggerConfig
from user_sim.utilities import *
from user_sim.data_gathering import *

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

class verbose:

    def __init__(self, show_print):
        self.print_list = []
        self.show_print = show_print

    def add(self, log):
        self.print_list.add(log)

    def add_show(self, log):
        self.print_list.add(log)
        if self.show_print:
            print(log)

    def show(self):
        if self.show_print:
            for log in self.print_list:
                print(log)

    def reset_verbose(self):
        self.print_list = []
 #disabled


class user_generation:

    def __init__(self, user_profile, chatbot, enable_logs=True):

        self.user_profile = user_profile
        self.chatbot = chatbot
        self.logger_config = LoggerConfig(mostrar_logs=enable_logs)
        self.logger = logging.getLogger('my_logger')  #???
        self.temp = user_profile.temperature
        self.user_llm = ChatOpenAI(model="gpt-4o", temperature=self.temp)
        self.conversation_history = {'interaction':[]}
        self.ask_about = list_to_phrase(user_profile.ask_about, prompted=True)
        self.request_register = user_assistant(user_profile.ask_about)
        self.data_gathering = chatbot_assistant(user_profile.ask_about)
        self.user_role_prompt = PromptTemplate(
            input_variables=["reminder", "history"],
            template=self.set_role_template()
        )

        self.test_name = user_profile.test_name
        self.repeat_count = 0
        self.loop_count = 0
        self.interaction_count = 0
        self.user_chain = LLMChain(llm=self.user_llm, prompt=self.user_role_prompt)



    def add_context(self, msg: list[dict]):
        self.context.append(msg)

    def set_role_template(self):
       reminder = """{reminder}"""
       history = """History of the conversation so far: {history}"""
       role_prompt = self.user_profile.role + reminder + history
       return role_prompt


    def add_register(self, msg: list[dict]):
        self.conv_register = self.conv_register + msg

    # def save_conversation(self, path):
    #     print("Saving conversation...")
    #     # save_test_conv(self.conversation_history, self.test_name, path)
    #     print("Conversation saved!")

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

        initial_context = (self.user_profile.language +
                           self.user_profile.context +
                           self.user_profile.interaction_styles +
                           self.ask_about)

        if nlp_processor(response, self.chatbot.fallback, 0.6):
            self.repeat_count += 1
            self.loop_count += 1
            self.logger.info("is end")


            if self.repeat_count >= reps:
                self.repeat_count = 0
                change_topic = "Since the assistant is not understanding what you're saying, change the topic to other things to ask about without starting a new conversation"
                reminder = initial_context + change_topic
                return reminder

            else:
                ask_repetition = "If the assistant asks you to repeat the question, repeat the last question the user said but rephrase it."
                reminder = initial_context + ask_repetition
                return reminder


        else:
            self.repeat_count = 0
            self.loop_count = 0

            return initial_context

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
        self.conversation_history['interaction'].append({role:message})


    def end_conversation(self, input_msg):

        if self.interaction_count >= self.user_profile.goal_style[1] and self.user_profile.goal_style[0] == 'steps':
            self.logger.info("is end")
            return True

        # elif self.interaction_count >= 10 and self.user_profile.goal_style[0] == 'several steps':
        #     self.logger.info("is end")
        #     return True

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

        reminder = self.repetition_track(input_msg)
        history = self.get_history()

        # Generar la respuesta del usuario
        user_response = self.user_chain.run(history=history, reminder=reminder)
        self.request_register.get_request(user_response)

        self.update_history("User", user_response)

        self.interaction_count += 1

        return user_response


    @staticmethod
    def formatting(role, msg):
        return [{"role": role, "content": msg}]


    def open_conversation(self):
        print(type(self.user_profile.language))

        initial_context = (self.user_profile.language +
                           self.user_profile.context +
                           self.user_profile.goal_style[0] +
                           self.user_profile.interaction_styles +
                           self.ask_about)

        history = self.get_history()
        user_response = self.user_chain.run(history=history, reminder=initial_context)  # generation of user message

        self.update_history("User", user_response)

        self.request_register.get_request(user_response)
        self.interaction_count += 1
        return user_response