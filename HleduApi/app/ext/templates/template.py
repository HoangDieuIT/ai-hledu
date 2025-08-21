from pydantic import BaseModel, Field
from typing import Dict, Any
from app.service.types import TypeRequest, ModeRequest

class PromptTemplate(BaseModel):
    student_level: str = Field(...)
    topic: str = Field(...)
    text: str = Field(...)
    type: TypeRequest = Field(..., description="Granularity")
    mode: ModeRequest = Field(..., description="Task mode")

    def _system_writing(self) -> str:
        return (
            f"You are an expert ESL writing assessor for {self.student_level} level students. "
            f"Evaluate the {self.type.name.lower()} on topic '{self.topic}' objectively and precisely. "
            "Provide scores from 0-10 for Grammar, Vocabulary, Coherence, and Content. "
            "Return detailed JSON assessment with specific feedback and suggestions. "
            "Be constructive and educational in your feedback."
        )

    def _user_writing(self) -> str:
        json_structure = '''{
  "overall_score": 8.5,
  "grammar_score": 8.0,
  "vocabulary_score": 7.5,
  "coherence_score": 9.0,
  "content_score": 8.5,
  "general_feedback": "Overall assessment summary",
  "detailed_feedback": "Comprehensive analysis of strengths and areas for improvement",
  "grammar_errors": [
    {
      "error_type": "Subject-verb agreement",
      "original_text": "The cats was playing",
      "corrected_text": "The cats were playing",
      "explanation": "Plural subject requires plural verb",
      "line_number": 1
    }
  ],
  "grammar_improvements": ["Focus on subject-verb agreement", "Practice with irregular verbs"],
  "vocabulary_suggestions": [
    {
      "original_word": "big",
      "suggested_word": "enormous",
      "reason": "More precise and advanced vocabulary",
      "line_number": 2
    }
  ],
  "vocabulary_improvements": ["Use more varied adjectives", "Learn academic vocabulary"],
  "improvement_suggestions": ["Work on paragraph structure", "Use transition words"],
  "suggested": "Here is an improved version of your writing..."
}'''

        return (
            f"Please assess this {self.type.name.lower()} written by a {self.student_level} level student.\n\n"
            f"Topic: {self.topic}\n\n"
            f"Student Text:\n{self.text}\n\n"
            "Provide a comprehensive assessment following this exact JSON format:\n"
            f"{json_structure}\n\n"
            "Requirements:\n"
            "- Scores must be numbers between 0-10\n"
            "- Provide specific, actionable feedback\n"
            "- Include concrete examples in error corrections\n"
            "- Make suggestions appropriate for the student level\n"
            "- Return ONLY valid JSON, no additional text"
        )

    def build(self) -> Dict[str, Any]:
        """Build messages for writing assessment"""
        messages = [
            {"role": "system", "content": self._system_writing()},
            {"role": "user", "content": self._user_writing()}
        ]
        return {"messages": messages}