import enum
from enum import Enum

class TypeRequest(Enum):
    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    ESSAY = "essay"


class ModeRequest(Enum):
    WRITING = "writing"
    SPEAKING = "speaking"


