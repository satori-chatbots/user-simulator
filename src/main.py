import openai
import yaml
import os

openai.api_key = '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'


class interaction:

    def __init__(self, user_profile):
        self.user_profile = user_profile

    def generar_interaccion(self, msg, temperatura=0.5, max_tokens=300):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=msg,
            temperature=temperatura,
            max_tokens=max_tokens
        )
        return response['choices'][0]['message']['content'].strip()


    def read_yaml(self, file):
        with open(file, 'r') as f:
            interactions = yaml.safe_load(f)
        return interactions


    @staticmethod
    def list_to_phrase(s_list: list):

        #s_list: list of strings
        #l_string: string values extracted from s_list in string format

        l_string = s_list[0]

        if len(s_list) <= 1:
            return s_list

        else:
            for i in range(len(s_list) - 1):
                if s_list[i + 1] == s_list[-1]:
                    l_string = f"{l_string} or {s_list[i + 1]}"
                else:
                    l_string = f"{l_string}, {s_list[i + 1]}"
            return l_string

    def conversation(self):

        user_act = self.read_yaml(self.user_profile)
        msg = [{"role": "system",
                "content": user_act["context"][0]}]
        keep_context = user_act["keep_context"][0]
        ask_about = interaction.list_to_phrase(user_act["ask_about"])

        while True:
            prompt = input("input (you're the assistant): ")
            if prompt.lower() == "exit":
                print("Bye!")
                break  # Salir del bucle si el usuario escribe 'salir'

            #respuesta = generar_respuesta(mensaje_usuario)
            #print(respuesta)

            #print(f"assistant: {prompt}")
            user_response = self.generar_interaccion(msg + [{"role": "assistant",
                                                             "content": prompt + keep_context + ask_about}])
            print(f"user: {user_response}")
            msg = msg + [{"role": "user", "content": user_response}]


def main():

    user_profile = "yaml/user_sim.yml"

    interaction(user_profile).conversation()

main()
