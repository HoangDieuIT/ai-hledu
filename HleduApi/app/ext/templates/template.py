from typing import Literal
from pydantic import BaseModel, Field
from app.service.types import TypeRequest, ModeRequest
from .base import WritingAssessmentTemplate, SpeakingAssessmentTemplate


class PromptTemplate(BaseModel):
    """
    Scalable prompt builder across modes (writing/speaking) and granularities.
    """

    student_level: str = Field(...)
    topic: str = Field(...)
    text: str = Field(...)
    type: Literal[
        TypeRequest.WORD,
        TypeRequest.SENTENCE,
        TypeRequest.PARAGRAPH,
        TypeRequest.ESSAY,
    ] = Field(..., description="Granularity")
    mode: Literal[ModeRequest.WRITING, ModeRequest.SPEAKING] = Field(..., description="Task mode")

    def _system_for_writing(self) -> str:
        match self.type:
            case TypeRequest.WORD:
                focus = "a word"
            case TypeRequest.SENTENCE:
                focus = "a sentence"
            case TypeRequest.PARAGRAPH:
                focus = "a paragraph"
            case TypeRequest.ESSAY:
                focus = "an essay"
            case _:
                focus = "text"
        return (
            "You are a helpful assistant for writing assessment. "
            f"You are given {focus} and must evaluate it objectively."
        )

    def _system_for_speaking(self) -> str:
        return (
            "You are a helpful assistant for speaking assessment. "
            "Evaluate pronunciation, fluency, coherence, and vocabulary usage."
        )

    def _user_common(self) -> str:
        return (
            f"Topic: {self.topic}\n"
            f"Student Level: {self.student_level}\n"
            f"Text: {self.text}\n"
        )

    def _user_for_writing(self) -> str:
        return (
            self._user_common()
            + "\nPlease analyze and provide:\n"
            + "1. Overall score (0-10)\n"
            + "2. Individual scores for Grammar, Vocabulary, Coherence, Content (0-10 each)\n"
            + "3. General feedback (overall impression)\n"
            + "4. Detailed feedback (comprehensive analysis)\n"
            + "5. Grammar errors with corrections\n"
            + "6. Vocabulary suggestions\n"
            + "7. Improvement suggestions\n"
            + "8. An improved version of the writing\n"
            + "\nFormat response as JSON with fields similar to the writing template."
        )

    def _user_for_speaking(self) -> str:
        return (
            self._user_common()
            + "\nPlease analyze and provide:\n"
            + "1. Overall speaking score (0-10)\n"
            + "2. Scores for Pronunciation, Fluency, Coherence, Vocabulary (0-10 each)\n"
            + "3. Specific pronunciation errors and corrections\n"
            + "4. Fluency feedback and pace suggestions\n"
            + "5. Recommended practice drills\n"
            + "\nFormat response as JSON with analogous fields."
        )

    def build(self) -> str:
        if self.mode is ModeRequest.WRITING:
            t = WritingAssessmentTemplate(
                student_level=self.student_level,
                topic=self.topic,
                text=self.text,
                type=self.type,
            )
        else:
            t = SpeakingAssessmentTemplate(
                student_level=self.student_level,
                topic=self.topic,
                text=self.text,
                type=self.type,
            )
        return f"<SYSTEM>\n{t.system_prompt()}\n</SYSTEM>\n<USER>\n{t.user_prompt()}\n</USER>"

