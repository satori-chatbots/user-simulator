from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Any
from types import SimpleNamespace

from .rule_utils import *

from metamorphic.tests import Test


class Rule(BaseModel):
    name: str
    description: str
    conversations: int = 1
    active: Optional[bool] = True
    when: Optional[str] = "True"
    if_: Optional[str] = Field("True", alias="if")
    then: str

    @model_validator(mode='before')
    @classmethod
    def check_aliases(cls, values: Any) -> Any:
        # Handle 'oracle' or 'then' interchangeably
        if 'oracle' in values:
            values['then'] = values.pop('oracle')
        return values

    def test(self, tests: List[Test], verbose: bool = False) -> dict:
        print(f" - Checking rule {self.name} [conversations: {self.conversations}]")
        if self.conversations == 1:
            return self.__property_test(tests, verbose)
        else:
            return self.__metamorphic_test(tests, verbose)

    def __property_test(self, tests: List[Test], verbose: bool) -> dict:
        results = {'pass': [], 'fail': [], 'not_applicable': []}
        for test in tests:
            test_dict = test.to_dict()
            conv = [SimpleNamespace(**test_dict)]
            test_dict['conv'] = conv
            test_dict.update(util_functions_to_dict())
            if verbose:
                print(f"   - On file {test.file_name}")
            if self.applies(test_dict):
                if self.if_eval(test_dict):
                    if self.then_eval(test_dict):
                        results['pass'].append(test.file_name)
                        if verbose:
                            print(f"     -> Satisfied!")
                    else:
                        results['fail'].append(test.file_name)
                        if verbose: print(f"     -> NOT Satisfied!")
                else:
                    results['not_applicable'].append(test.file_name)
                    if verbose: print(f"     -> Does not apply.")
            else:
                results['not_applicable'].append(test.file_name)
                if verbose: print(f"     -> Does not apply.")
        return results

    def __metamorphic_test(self, tests: List[Test], verbose: bool) -> dict:
        results = {'pass': [], 'fail': [], 'not_applicable': []}
        for test1 in tests:
            test_dict1 = test1.to_dict()
            sns = SimpleNamespace(**test_dict1)
            conv = [sns, sns]
            test_dict = {'conv': conv}
            test_dict.update(util_functions_to_dict())
            for test2 in tests:
                if test1 == test2:
                    continue
                test_dict2 = test2.to_dict()
                conv[1] = SimpleNamespace(**test_dict2)
                if verbose:
                    print(f"   - On files: {test1.file_name}, {test2.file_name}")
                if self.applies(test_dict):
                    if self.if_eval(test_dict):
                        if self.then_eval(test_dict):
                            results['pass'].append((test1.file_name, test2.file_name))
                            if verbose: print(f"     -> Satisfied!")
                        else:
                            results['fail'].append((test1.file_name, test2.file_name))
                            if verbose: print(f"     -> NOT Satisfied!")
                    else:
                        results['not_applicable'].append((test1.file_name, test2.file_name))
                        if verbose: print(f"     -> Does not apply.")
                else:
                    results['not_applicable'].append((test1.file_name, test2.file_name))
                    if verbose: print(f"     -> Does not apply.")
        return results

    def applies(self, test_dict: dict):
        return eval(self.when, test_dict)

    def if_eval(self, test_dict: dict):
        return eval(self.if_, test_dict)

    def then_eval(self, test_dict: dict):
        return eval(self.then, test_dict)
