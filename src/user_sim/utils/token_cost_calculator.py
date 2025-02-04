from PIL import Image
import requests
import base64
from io import BytesIO
import re
import os
import tiktoken
import pandas as pd
import logging
from user_sim.utils import config
from user_sim.utils.config import total_cost, token_count_enabled
from user_sim.utils.utilities import get_encoding

logger = logging.getLogger('Info Logger')

columns = ["Conversation", "Test Name", "Module", "Model", "Total Cost",
           "Timestamp", "Input Cost", "Input Message",
           "Output Cost", "Output Message"]

PRICING = {
    "gpt-4o": {"input": 2.5 / 10**6, "output": 10 / 10**6},
    "gpt-4o-mini": {"input": 0.15 / 10**6, "output": 0.6 / 10**6},
    "whisper": 0.006/60,
    "tts-1": 0.0015/1000  # (characters, not tokens)
}

TOKENS = {
    "gpt-4o": {"input": 10**6/2.5, "output": 10**6/10},
    "gpt-4o-mini": {"input": 10**6/0.15, "output": 10**6/0.6},
    "whisper": 60/0.006,
    "tts-1": 1000/0.0015  # (characters, not tokens)
}

def create_cost_dataset(serial, test_cases_folder):
    folder = f"{test_cases_folder}/__cost_report__"
    file = f"cost_report_{serial}.csv"
    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created cost report folder at: {folder}")

    path = f"{folder}/{file}"

    cost_df = pd.DataFrame(columns=columns)
    cost_df.to_csv(path, index=False)
    config.cost_ds_path = path
    logger.info(f"Cost dataframe created at {path}.")


def count_tokens(text, model="gpt-4o-mini"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def calculate_text_cost(tokens, model="gpt-4o-mini", io_type="input"):
    cost = tokens * PRICING[model][io_type]
    return cost


def calculate_image_cost(image):
    def get_dimensions(image_input):
        try:
            if isinstance(image_input, bytes):
                image_input = image_input.decode('utf-8')
            if re.match(r'^https?://', image_input) or re.match(r'^http?://', image_input):  # Detects if it's a URL
                response = requests.get(image_input)
                response.raise_for_status()  #
                image = Image.open(BytesIO(response.content))
            else:
                decoded_image = base64.b64decode(image_input)
                image = Image.open(BytesIO(decoded_image))

            # Get the dimensions
            w, h = image.size
            return w, h
        except Exception as e:
            logger.error(e)
            return None

    dimensions = get_dimensions(image)
    if dimensions is None:
        logger.warning("Couldn't get image dimensions.")
        return None
    width, height = dimensions

    # Initial configuration
    price_per_million_tokens = 0.15
    tokens_per_tile = 5667
    base_tokens = 2833

    # Calculate the number of tiles needed (512 x 512 pixels)
    horizontal_tiles = (width + 511) // 512
    vertical_tiles = (height + 511) // 512
    total_tiles = horizontal_tiles * vertical_tiles

    # Calculate the total tokens
    total_tokens = base_tokens + (tokens_per_tile * total_tiles)

    # Convert tokens to price
    total_price = (total_tokens / 1_000_000) * price_per_million_tokens

    return total_price



# VISION
def input_vision_module_cost(input_message, image, model):
    input_tokens = count_tokens(input_message, model)
    image_cost = calculate_image_cost(image)
    if image_cost is None:
        logger.warning("Image cost set to $0.")
        image_cost = 0

    model_pricing = PRICING[model]
    input_cost = input_tokens * model_pricing["input"] + image_cost
    return input_cost
def output_vision_module_cost(output_message, model):
    output_tokens = count_tokens(output_message, model)
    model_pricing = PRICING[model]
    output_cost = output_tokens * model_pricing["output"]
    return output_cost

# TTS-STT
def input_tts_module_cost(input_message, model):
    model_pricing = PRICING[model]
    input_cost = len(input_message) * model_pricing
    return input_cost
def whisper_module_cost(audio_length, model):
    audio_length = audio_length
    model_pricing = PRICING[model]
    input_cost = audio_length * model_pricing
    return input_cost

# TEXT
def input_text_module_cost(input_message, model):
    input_tokens = count_tokens(input_message, model)
    model_pricing = PRICING[model]
    input_cost = input_tokens * model_pricing["input"]
    return input_cost
def output_text_module_cost(output_message, model):
    output_tokens = count_tokens(output_message, model)
    model_pricing = PRICING[model]
    output_cost = output_tokens * model_pricing["output"]
    return output_cost


def calculate_cost(input_message='', output_message='', model="gpt-4o", module=None, **kwargs):
    input_tokens = count_tokens(input_message, model)
    output_tokens = count_tokens(output_message, model)

    if model not in PRICING:
        raise ValueError(f"Pricing not available for model: {model}")

    if model == "whisper":
        total_cost = whisper_module_cost(kwargs.get("audio_length", None), model)

    elif model == "tts_1":
        input_cost = input_tts_module_cost(input_message, model)
        total_cost = input_cost

    elif kwargs.get("image", None):
        input_cost = input_vision_module_cost(input_message, kwargs.get("image", None), model)
        output_cost = output_vision_module_cost(output_message, model)
        total_cost = input_cost + output_cost

    else:
        input_cost = input_text_module_cost(input_message, model)
        output_cost = output_vision_module_cost(output_message, model)
        total_cost = input_cost + output_cost


    def update_dataframe():
        new_row = {"Conversation": config.conversation_name, "Test Name": config.test_name, "Module": module,
                   "Model": model, "Total Cost": total_cost, "Timestamp": pd.Timestamp.now(),
                   "Input Cost": input_cost, "Input Message": input_message,
                   "Output Cost": output_cost, "Output Message": output_message}

        encoding = get_encoding(config.cost_ds_path)["encoding"]
        cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)
        cost_df.loc[len(cost_df)] = new_row
        cost_df.to_csv(config.cost_ds_path, index=False)

        config.total_cost = float(cost_df['Total Cost'].sum())

        logger.info("Updated 'cost_report' dataframe with new cost.")

    update_dataframe()

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }


def get_cost_report(test_cases_folder):
    export_path = test_cases_folder + f"/__cost_report__"
    serial = config.serial
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    export_file_name = export_path + f"/report_{serial}.csv"

    encoding = get_encoding(config.cost_ds_path)["encoding"]
    temp_cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)
    temp_cost_df.to_csv(export_file_name, index=False)

    # config.cost_ds_path.close()
    # os.remove(temp_file.name)


def calculate_input_tokens(input_message, model=config.model):
    if max_input_tokens_allowed(model, ):
        return True
    else:
        input_cost = count_tokens(input_message, model) * PRICING[model]["input"]
        config.total_cost += input_cost
        config.total_individual_cost += input_cost


def calculate_output_tokens(input_message, model=config.model):
    output_cost = count_tokens(input_message, model) * PRICING[model]["output"]
    config.total_cost += output_cost
    config.total_individual_cost += output_cost

def max_input_tokens_allowed(text='', model_used='gpt-4o-mini', **kwargs):

    def get_delta_verification(sim_cost, sim_ind_cost):
        delta_cost = config.limit_cost - sim_cost
        delta_individual_cost = config.limit_individual_cost - sim_ind_cost
        logger.info(f"${delta_cost} for global and ${delta_individual_cost} for individual input cost left.")
        return True if delta_cost <= 0 or delta_individual_cost <= 0 else False

    if config.token_count_enabled:
        if kwargs.get("image", None):
            input_cost = input_vision_module_cost(text, kwargs.get("image", 0), model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
        elif model_used == "tts-1":
            input_cost = input_tts_module_cost(text, model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
        elif model_used == "whisper":
            input_cost = whisper_module_cost(kwargs.get("audio_length", 0), model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
        else:
            input_cost = input_text_module_cost(text, model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
    else:
        return False

def max_output_tokens_allowed(model_used):
    if token_count_enabled:
        delta_cost = config.limit_cost - config.total_cost
        delta_individual_cost = config.limit_individual_cost - config.total_individual_cost

        delta = min([delta_cost, delta_individual_cost])
        output_tokens = delta * TOKENS[model_used]["output"]
        logger.info(f"{output_tokens} output tokens left.")
        return output_tokens
    else:
        return