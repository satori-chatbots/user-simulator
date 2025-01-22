from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage
import fitz
import base64
import re
from urllib.parse import urlparse
import os
import requests
import hashlib

import json
import logging
from user_sim.image_recognition_module import image_description
logger = logging.getLogger('Info Logger')
chat = ChatOpenAI(model="gpt-4o-mini")

current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_script_dir, "../.."))
temp_file_dir = os.path.join(project_root, "temp_files")
hash_register_path = os.path.join(temp_file_dir, "hash_register.json")


def load_pdf_register():
    if not os.path.exists(temp_file_dir):
        os.makedirs(temp_file_dir)
        return {}
    else:
        if not os.path.exists(hash_register_path):
            with open(hash_register_path, 'w') as file:
                json.dump({}, file)
            return {}
        else:
            with open(hash_register_path, 'r') as file:
                hash_reg = json.load(file)
            return hash_reg


def hash_generate(pdf_path):
    hasher = hashlib.md5()
    with open(pdf_path, 'rb') as pdf_file:
        buf = pdf_file.read()
        hasher.update(buf)
    return hasher.hexdigest()


def save_pdf_register(hash_register):
    with open(hash_register_path, 'w') as file:
        json.dump(hash_register, file, ensure_ascii=False, indent=4)

def clear_pdf_register():
    with open(hash_register_path, 'w') as file:
        json.dump({}, file)

def pdf_reader(pdf, ignore_cache=False, update_cache=False):

    # register = {} if ignore_cache else load_pdf_register()
    if ignore_cache:
        register = {}
        logger.info("Cache will be ignored.")
    else:
        register = load_pdf_register()

    pdf_hash = hash_generate(pdf)

    def process_pdf(pdf_file):
        doc = fitz.open(pdf_file)
        plain_text = ""
        for page_number in range(len(doc)):
            page = doc.load_page(page_number)
            plain_text += f"Page nª{page_number}: {page.get_text()} "

            images = page.get_images(full=True)
            if images:
                plain_text += f"Images in this page: "
                for img_index, img in enumerate(images):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_base64 = base64.b64encode(image_bytes)
                    description = image_description(image_base64, url=False, ignore_cache=ignore_cache, update_cache=update_cache)
                    plain_text += f"Image description {img_index + 1}: {description}"
        return f"(PDF content: {plain_text} >>)"

    if pdf_hash in register:
        if update_cache:
            output_text = process_pdf(pdf)
            register[pdf_hash] = output_text
            logger.info("Cache updated!")
        output_text = register[pdf_hash]
        logger.info("Retrieved information from cache.")

    else:
        output_text = process_pdf(pdf)
        register[pdf_hash] = output_text

    if ignore_cache:
        logger.info("PDF cache was ignored.")
    else:
        save_pdf_register(register)
        logger.info("PDF cache was saved!")

    logger.info(output_text)
    return output_text


def get_pdf(match):
    response = requests.get(match)
    content_type = response.headers.get('Content-Type', '').lower()
    filename = None
    content_disposition = response.headers.get('Content-Disposition', '')
    if 'application/pdf' in content_type:
        extension = ".pdf"

        pdfs_dir = os.path.join(project_root, "pdfs")

        if not os.path.exists(pdfs_dir):
            os.makedirs(pdfs_dir)

        if 'filename=' in content_disposition:
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                filename = filename_match.group(1)

        if not filename:
            parsed_url = urlparse(match)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = 'pdf_download'
            if extension and not filename.endswith(extension):
                filename += extension

        full_path = os.path.join(pdfs_dir, filename)
        content = response.content

        with open(full_path, 'wb') as f:
            f.write(content)

        return full_path

    else:
        return None