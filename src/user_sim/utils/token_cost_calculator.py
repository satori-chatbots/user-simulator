from PIL import Image
import requests
import base64
from io import BytesIO
import re
import tiktoken
import pandas as pd
import tempfile
import logging
logger = logging.getLogger('Info Logger')

columns = ["Module", "Total Cost", "Timestamp", "Input Cost", "Input Message", "Output Cost", "Output Message"]
cost_df = pd.DataFrame(columns=columns)
temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
cost_df.to_csv(temp_file.name, index=False)
logger.info("Cost dataframe created as temporary file.")

PRICING = {
    "gpt-4o": {"input": 2.5 / 10**6, "output": 10 / 10**6},
    "gpt-4o-mini": {"input": 0.15 / 10**6, "output": 0.6 / 10**6},
    "whisper": 0.006/60,
    "tts-1": 15/10**10
}


def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))


def calculate_image_cost(image):
    def get_dimensions(image_input):
        try:
            if re.match(r'^https?://', image_input) or re.match(r'^http?://', image_input):  # Detects if it's a URL
                response = requests.get(image_input)
                response.raise_for_status()  #
                image = Image.open(BytesIO(response.content))
            else:
                decoded_image = base64.b64decode(image_input)
                image = Image.open(BytesIO(decoded_image))

            # Get the dimensions
            width, height = image.size
            return width, height
        except Exception as e:
            return f"Error processing the image: {e}"

    width, height = get_dimensions(image)
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
        new_row = {"Module": module, "Total Cost": total_cost, "Timestamp": pd.Timestamp.now(),
                   "Input Cost": input_cost, "Input Message": input_message,
                   "Output Cost": output_cost, "Output Message": output_message}

        temp_cost_df = pd.read_csv(temp_file)
        temp_cost_df.loc[len(temp_cost_df)] = new_row
        temp_cost_df.to_csv(temp_file)
        logger.info("Updated 'cost dataframe with new cost.")

    update_dataframe()

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }














