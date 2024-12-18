from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
import fitz
import base64
import re
from urllib.parse import urlparse
import os
import requests
import logging
logger = logging.getLogger('Info Logger')
chat = ChatOpenAI(model="gpt-4o")


def image_description(image):
    chat = ChatOpenAI(model="gpt-4o")
    output = chat.invoke(
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "describe this image in one line with the important details"
                    },
                    {
                        "type": "image_url",
                        "image_url": { "url": f"data:image/png;base64,{image}" }
                    }
                ]

            )
        ]
    )
    output_text = output.content
    return output_text

def pdf_reader(pdf):
    doc = fitz.open(pdf)
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
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                description = image_description(image_base64)
                plain_text += f"Image description {img_index+1}: {description}"
    output_text = f"(PDF content: {plain_text} >>)"
    logger.info(output_text)
    return output_text


def get_pdf(match):
    response = requests.get(match)
    content_type = response.headers.get('Content-Type', '').lower()
    filename = None
    content_disposition = response.headers.get('Content-Disposition', '')
    if 'application/pdf' in content_type:
        extension = ".pdf"

        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_script_dir, "../.."))
        pdfs_dir = os.path.join(project_root, "pdfs")

        if not os.path.exists(pdfs_dir):
            os.makedirs(pdfs_dir)

        if 'filename=' in content_disposition:
            # Extraemos el filename del Content-Disposition (si está entre comillas o no)
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


# def process_pdf(matches):
#
#     get_pdf(matches)
#
#     if os.path.exists(pdfs_path):
#         full_path = os.path.join(self.pdfs_path, self.pdfs_list[-1])
#         full_text = pdf_reader(full_path)
#         return full_text





# text = "La EPS imparte los siguientes grados: <a href='https://www.uam.es/EPS/documento/1446848909624/tfms---plazos-para-tramitar-2024-25.pdf?blobheader=application/pdf'>Aquí</a> está. "
#
# get_pdf(text)
#
# # url = "pdfs/Normativa_TFMs_EPS.pdf"
# # op = pdf_reader(url)
# # print(op)