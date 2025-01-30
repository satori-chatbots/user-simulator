import math
from user_sim.interaction_styles import *
from user_sim.utils.token_cost_calculator import count_tokens, calculate_text_cost
from user_sim.utils import config
from user_sim.utils.languages import languages_weights


predictable = {
    "any_list": {
        "input_message": "",
        "times_executed": 0,
        "padding": 0.2
    },
    "data_gathering": {
        "input_message": "",
        "padding": 0.3
    },
    "data_extraction": {
        "input_message": "",
        "padding": 0.3
    }
}

pers = {
    "conversational-user": 2,
    "curious-user": 1,
    "direct-user": 1,
    "disorganized-user": 1,
    "elderly-user": 1,
    "formal-user": 1,
    "impatient-user": 1,
    "rude-user": 1,
    "sarcastic-user": 1,
    "skeptical-user:": 1,
}



average_token_per_interaction = 50 # not accurate


class CostEstimator:

    def __init__(self, model, conversation_number, conversation_steps, context, personality, interaction_styles):

        self.model = model
        self.conversation_number = conversation_number
        self.conversation_steps = conversation_steps
        self.context = context
        self.personality = personality
        self.interaction_styles = interaction_styles

        # static
        context_cost = self.calculate_cost_context(self.context)
        personality_cost = self.calculate_cost_personality()
        interaction_styles_cost = self.calculate_cost_interaction_styles()

        # dynamic
        any_list_cost = self.calculate_cost_any_list()
        data_gathering_cost = self.calculate_cost_data_gathering()
        data_extraction_cost = self.calculate_cost_data_extraction()

        self.total_cost = self.sum_cost(context_cost,
                                        personality_cost,
                                        interaction_styles_cost,
                                        any_list_cost,
                                        data_gathering_cost,
                                        data_extraction_cost)

    @staticmethod
    def sum_cost(*args):
        return sum(args)

    def get_ch_lang_weight(self):
        language_list = self.interaction_styles.languages_options
        weight_list = []
        for language in language_list:
            weight_list.append(languages_weights[language])

        max_weight = max(weight_list)
        final_weight = max_weight*self.interaction_styles.chance

        return final_weight


# static cost
    def calculate_cost_context(self, context):
        tokens_context = count_tokens(context, self.model)
        tokens_default_context = count_tokens(config.default_context, self.model)
        tokens_inter_style_context = sum([count_tokens(inter_s.get_prompt, self.model) for inter_s in self.interaction_styles])
        total_tokens = sum(tokens_context, tokens_default_context, tokens_inter_style_context)

        total_cost = calculate_text_cost(total_tokens, self.model) * self.conversation_steps * self.conversation_number

        return total_cost

# weighted cost
    def get_personality_weight(self):
        if self.personality:
            weight = pers[self.personality]
        else:
            weight = 1
        return weight

    def get_inter_sty_weight(self):
        weights = {
            'long phrases': 1,
            'change your mind': 1,
            'change language': self.get_ch_lang_weight(),
            'make spelling mistakes': 1,
            'single questions': 1,
            'all questions': 1,
            'default': 1
        }
        inter_weight_list = []
        for inter_instance in self.interaction_styles:
            inter_weight_list.append(weights[inter_instance.inter_type])

        return inter_sty_weight

    def estimate_output_cost(self):
        def estimate_cost(*args):
            tokens = average_token_per_interaction * self.conversation_steps * self.conversation_number * args
            total_tokens = math.ceil(tokens)
            cost = calculate_text_cost(total_tokens, self.model, io_type="output")
            return cost

        total_cost = estimate_cost(self.get_personality_weight(), self.get_inter_sty_weight())



# llm-based module cost
    def calculate_cost_any_list(self):
        pass

    def calculate_cost_data_gathering(self):
        pass

    def calculate_cost_data_extraction(self):
        pass








instance = None

def initialize_class(param1, param2):
    global instance
    instance = CostEstimator(param1, param2)
