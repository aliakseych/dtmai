from src.interfaces.mongodb.repositories.attempts import AttemptRepository
from src.interfaces.mongodb.repositories.categories import CategoryRepository
from src.interfaces.mongodb.repositories.programs import ProgramRepository
from src.interfaces.mongodb.repositories.questions import QuestionRepository
from src.interfaces.mongodb.repositories.sources import SourceRepository
from src.interfaces.mongodb.repositories.users import UserRepository

__all__ = [
    "AttemptRepository",
    "CategoryRepository",
    "ProgramRepository",
    "QuestionRepository",
    "SourceRepository",
    "UserRepository",
]