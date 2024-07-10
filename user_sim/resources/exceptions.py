# class EmptyListException(Exception):
#     def __init__(self, message="La lista está vacía"):
#         self.message = message
#         super().__init__(self.message)

class InvalidGoalException(Exception):
    pass


class InvalidInteractionException(Exception):
    pass


class InvalidLanguageException(Exception):
    pass