"""باكدج الموديولات (إعادة تصدير للتوافق مع from app.db.models import ...)."""

from app.db.models.base import Base
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.question import Question
from app.db.models.quiz import Quiz
from app.db.models.teacher import Teacher, TeacherGrade

__all__ = [
    "Base",
    "Conversation",
    "Message",
    "Question",
    "Quiz",
    "Teacher",
    "TeacherGrade",
]
