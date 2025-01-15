from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
import os
import logging
import json
logger = logging.getLogger('Info Logger')
chat = ChatOpenAI(model="gpt-4o-mini")

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, "../.."))
temp_file_dir = os.path.join(project_root, "temp_files")
image_register_path = os.path.join(temp_file_dir, "image_register.json")


def generate_image_description(image):
    output = chat.invoke(
        [
            HumanMessage(
                content=[
                    {"type": "text", "text": "describe in detail this image"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image,
                            "detail": "auto"
                        }
                    }
                ]

            )
        ]
    )
    output_text = f"(Image description: {output.content})"
    logger.info(output_text)
    return output_text


def update_image_register(register):
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


def image_description(image):
    register = load_image_register()

    if image in register:
        return register[image]

    description = generate_image_description(image)
    register[image] = description
    update_image_register(register)
    return description


