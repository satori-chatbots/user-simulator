from pydantic import BaseModel, Field
from typing import Optional, List

from metamorphic.tests import Test


class Rule(BaseModel):
    name: str
    description: str
    conversations: int = 1
    when: Optional[str] = "True"
    if_: str = Field(..., alias="if")
    then: str

    def test(self, tests: List[Test]):
        print(f" - Checking rule {self.name}")
        if self.conversations == 1:
            self.__property_test(tests)
        else:
            self.__metamorphic_test(tests)


    def __property_test(self, tests: List[Test]):
        for test in tests:
            print(f"   - On file {test.file_name}")
            if self.applies(test):
                print(f"     - Applies!")
                if self.if_eval(test):
                    print(f"     - If evals to True!")


    def __metamorphic_test(self, tests: List[Test]):
        print(f"   - (to be implemented)")


    def applies(self, test: Test):
        test_dict = test.to_dict()
        return eval(self.when, test_dict)


    def if_eval(self, test: Test):
        test_dict = test.to_dict()
        return eval(self.if_, test_dict)