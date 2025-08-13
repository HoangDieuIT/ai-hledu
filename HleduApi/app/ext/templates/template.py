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
        """
        Build the prompt for analyzing a writing task.
        Returns:
            str: A formatted string containing analysis instructions and JSON output format.
        """
        # Common instructions or context for the task
        base_prompt = self._user_common()

        # Detailed analysis requirements
        analysis_instructions = """
            Please analyze and provide:
            1. Overall score (0-10)
            2. Individual scores for Grammar, Vocabulary, Coherence, Content (0-10 each)
            3. General feedback (overall impression)
            4. Detailed feedback (comprehensive analysis)
            5. Grammar errors with corrections
            6. Vocabulary suggestions
            7. Improvement suggestions
            8. An improved version of the writing
            9. Format of response is JSON
            """

        # JSON format specification
        json_format = """
            Format your response as JSON with these fields:
            {
                "overall_score": float,
                "grammar_score": float,
                "vocabulary_score": float,
                "coherence_score": float,
                "content_score": float,
                "general_feedback": "string",
                "detailed_feedback": "string",
                "grammar_errors": [
                    {
                        "error_type": "string",
                        "original_text": "string",
                        "corrected_text": "string",
                        "explanation": "string"
                    }
                ],
                "grammar_improvements": ["string"],
                "vocabulary_suggestions": [
                    {
                        "original_word": "string",
                        "suggested_word": "string",
                        "reason": "string"
                    }
                ],
                "vocabulary_improvements": ["string"],
                "improvement_suggestions": ["string"],
                "suggested_writing": "string"
            }
            """

        # Combine all parts into one final prompt
        return f"{base_prompt}{analysis_instructions}{json_format}"

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

