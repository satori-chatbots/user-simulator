from pydantic import BaseModel, Field
from typing import List, Optional


class Test(BaseModel):
    ask_about: list
    conversation: list
    interaction: list
    language: Optional[str] = None
    serial: str
    file_name: Optional[str] = None

    @staticmethod
    def build_test(file, args):
        test = Test(**args)
        test.file_name = file
        return test


    def to_dict(self):
        print(f"Dict = {self.dict()}")
        return {'size': 'small', 'toppings': 'olives'}
