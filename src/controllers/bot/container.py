from src.interfaces.mongodb.client import MongoClient
from src.interfaces.mongodb.repositories.attempts import AttemptRepository
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.interfaces.mongodb.repositories.programs import ProgramRepository
from src.interfaces.mongodb.repositories.questions import QuestionRepository
from src.interfaces.mongodb.repositories.users import UserRepository


class Container:
    """Dependency container passed to all bot handlers via aiogram's data system."""

    def __init__(self, mongo: MongoClient):
        self.users = UserRepository(mongo)
        self.questions = QuestionRepository(mongo)
        self.categories = CategoryRepository(mongo)
        self.attempts = AttemptRepository(mongo)
        self.programs = ProgramRepository(mongo)