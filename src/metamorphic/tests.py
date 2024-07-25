from pydantic import BaseModel, Field
from typing import List, Optional


class Test(BaseModel):
    ask_about: list
    conversation: list
    data_output: list
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
        variable_dict = self.__get_ask_about_dict()
        variable_dict.update(self.__get_parameters_dict(self.conversation, 'conversation'))
        variable_dict.update(self.__get_parameters_dict(self.data_output, 'data_output'))
        #print(f"Dict = {variable_dict}")
        return variable_dict

    def __get_ask_about_dict(self):
        clean_dict = dict()
        for item in self.ask_about:
            if isinstance(item, dict):
                for key in item:
                    clean_dict[key] = item[key]
        return clean_dict

    def __get_parameters_dict(self, attribute, name):
        clean_dict = dict()
        for item in attribute:
            if isinstance(item, dict):
                clean_dict.update(self.__flatten_dict(name, item))
        return clean_dict

    def __flatten_dict(self, name, map):
        flatten_dict = dict()
        for key in map:
            if not isinstance(map[key], dict):
                flatten_dict[name + '_' + key] = map[key]
                flatten_dict[key] = map[key]
            else:
                flatten_dict.update(self.__flatten_dict(name + '_' + key, map[key]))
        return flatten_dict
