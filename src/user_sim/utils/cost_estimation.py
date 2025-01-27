predictable = {
    "any_list":{
        "input_message": "",
        "times_executed": 0,
        "padding": 0.2
    },
    "data_gathering":{
        "input_message": "",
        "padding": 0.3
    },
    "data_extraction":{
        "input_message": "",
        "padding": 0.3
    }
}


class CostEstimator:

    def __init__(self, conversation_number, conversation_steps):
        self.total_cost = 0
        self.conversation_number = conversation_number
        self.conversation_steps = conversation_steps
        #todo: add parameters





instance = None

def initialize_class(param1, param2):
    global instance
    instance = CostEstimator(param1, param2)
