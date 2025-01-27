from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
from .utils.token_cost_calculator import calculate_cost
import os
import logging
import json
import hashlib

logger = logging.getLogger('Info Logger')
model = "gpt-4o-mini"
chat = ChatOpenAI(model=model)

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, "../.."))
temp_file_dir = os.path.join(project_root, "temp_files")
image_register_path = os.path.join(temp_file_dir, "image_register.json")



def hash_generate(image):
    hasher = hashlib.md5()
    hasher.update(image)
    return hasher.hexdigest()


def generate_image_description(image, url=True):

    if not url:
        image_parsed = f"data:image/png;base64,{image.decode('utf-8')}"
    else:
        image_parsed = image
    prompt = "describe in detail this image"
    output = chat.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_parsed,
                            "detail": "auto"
                        }
                    }
                ]

            )
        ]
    )
    output_text = f"(Image description: {output.content})"
    logger.info(output_text)
    calculate_cost(prompt, output_text, model=model, module="image recognition module", image=image)

    return output_text


def save_image_register(register):
    with open(image_register_path, "w", encoding="utf-8") as file:
        json.dump(register, file, ensure_ascii=False, indent=4)


def load_image_register():
    if not os.path.exists(temp_file_dir):
        os.makedirs(temp_file_dir)
        return {}
    else:
        if not os.path.exists(image_register_path):
            with open(image_register_path, 'w') as file:
                json.dump({}, file)
            return {}
        else:
            with open(image_register_path, 'r') as file:
                image_reg = json.load(file)
            return image_reg


def image_description(image, url=True, ignore_cache=False, update_cache=False):
    if ignore_cache:
        register = {}
        logger.info("Cache will be ignored.")
    else:
        register = load_image_register()

    image_hash = hash_generate(image)

    if image_hash in register:
        if update_cache:
            description = generate_image_description(image, url)
            register[image_hash] = description
            logger.info("Cache updated!")
        # description = register[image_hash]
        logger.info("Retrieved information from cache.")
        return register[image_hash]
    else:
        description = generate_image_description(image, url)
        register[image_hash] = description

    if ignore_cache:
        logger.info("Images cache was ignored")
    else:
        save_image_register(register)
        logger.info("Images cache was saved!")

    return description

def clear_image_register():
    with open(image_register_path, 'w') as file:
        json.dump({}, file)
