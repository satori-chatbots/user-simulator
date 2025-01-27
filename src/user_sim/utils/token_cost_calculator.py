from PIL import Image
import requests
import base64
from io import BytesIO
import re
import os
import tiktoken
import pandas as pd
import tempfile
import logging
from user_sim.utils import config



from user_sim.utils.utilities import get_encoding

logger = logging.getLogger('Info Logger')

columns = ["Conversation", "Test Name", "Module", "Total Cost",
           "Timestamp", "Input Cost", "Input Message",
           "Output Cost", "Output Message"]

PRICING = {
    "gpt-4o": {"input": 2.5 / 10**6, "output": 10 / 10**6},
    "gpt-4o-mini": {"input": 0.15 / 10**6, "output": 0.6 / 10**6},
    "whisper": 0.006/60,
    "tts-1": 15/10**10
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


def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


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

def calculate_cost(input_message='', output_message='', model="gpt-4o", module=None, **kwargs):
    input_tokens = count_tokens(input_message, model)
    output_tokens = count_tokens(output_message, model)

    if model not in PRICING:
        raise ValueError(f"Pricing not available for model: {model}")

    if model == "whisper":
        audio_length = kwargs.get("audio_length", 0)
        model_pricing = PRICING[model]
        input_cost = None
        output_cost = None
        total_cost = audio_length * model_pricing

    elif model == "tts_1":
        model_pricing = PRICING[model]
        input_cost = input_message * model_pricing
        output_cost = None
        total_cost = input_cost

    elif (model == "gpt-4o" or model == "gpt-4o-mini") and kwargs.get("image", None):
        image_cost = calculate_image_cost(kwargs.get("image", None))
        model_pricing = PRICING[model]
        input_cost = input_tokens * model_pricing["input"] + image_cost
        output_cost = output_tokens * model_pricing["output"]
        total_cost = input_cost + output_cost

    else:
        model_pricing = PRICING[model]
        input_cost = input_tokens * model_pricing["input"]
        output_cost = output_tokens * model_pricing["output"]
        total_cost = input_cost + output_cost


    def update_dataframe():
        new_row = {"Conversation": config.conversation_name,"Test Name":config.test_name, "Module": module, "Total Cost": total_cost,
                   "Timestamp": pd.Timestamp.now(),
                   "Input Cost": input_cost, "Input Message": input_message,
                   "Output Cost": output_cost, "Output Message": output_message}

        encoding = get_encoding(config.cost_ds_path)["encoding"]
        temp_cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)
        temp_cost_df.loc[len(temp_cost_df)] = new_row
        temp_cost_df.to_csv(config.cost_ds_path, index=False)
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