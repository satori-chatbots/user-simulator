from langchain_openai import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage
import logging
logger = logging.getLogger('Info Logger')
chat = ChatOpenAI(model="gpt-4o")


def image_description(image):

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
