import logging
import json
import re
from typing import Dict, Any
from .base import service
from .commons import r, Errors
from app.ext.templates.template import PromptTemplate
from app.service.types import TypeRequest, ModeRequest
from app.ext.providers import LLMManager
from app.api.view.requests import WritingAssessmentRequest
from app.api.view.responses import WritingAssessmentResponse


# Định nghĩa các field chính một lần để tái sử dụng
SCORE_FIELDS = ["overall_score", "grammar_score", "vocabulary_score", "coherence_score", "content_score"]
REQUIRED_FIELDS = SCORE_FIELDS + ["general_feedback"]

@service
async def assess_writing(request: WritingAssessmentRequest) -> WritingAssessmentResponse:
    """
    Assess writing using AI provider
    """
    try:
        r.logger.info(f"Building prompt for {request.type} assessment")
        template = PromptTemplate(
            student_level=request.student_level,
            topic=request.topic,
            text=request.text,
            type=request.type,
            mode=request.mode
        )
        prompt = template.build()

        r.logger.info("Generating AI response")
        llm_response = await LLMManager().generate(prompt)

        r.logger.info("Parsing AI response")
        assessment_data = _parse_ai_response(llm_response.content)

        return WritingAssessmentResponse(
            **assessment_data,
            provider_used=llm_response.provider_name,
            model_used=llm_response.model_name
        )

    except Exception as e:
        r.logger.error(f"Assessment failed: {str(e)}")
        return Errors.IO_ERROR.on(message="Failed to respond writing")


def _parse_ai_response(response: Any) -> Dict[str, Any]:
    """
    Parse AI raw response (Gemini/OpenAI/etc.) into WritingAssessmentResponse-compatible dict
    """
    try:
        # Nếu là list/dict thì convert sang string
        if isinstance(response, (list, dict)):
            response = json.dumps(response)

        # Tìm JSON object trong text
        match = re.search(r'\{[\s\S]*\}', str(response))
        json_str = match.group(0) if match else str(response)

        data = json.loads(json_str)

    except (json.JSONDecodeError, AttributeError):
        r.logger.warning("JSON parse failed, extracting from text")
        return _extract_from_text(str(response))

    # Map field còn thiếu
    for field in REQUIRED_FIELDS:
        if field not in data:
            r.logger.warning(f"Missing required field: {field}, extracting fallback value")
            data[field] = _extract_from_text(json_str).get(field)

    # Chuẩn hóa score
    for field in SCORE_FIELDS:
        if field in data:
            try:
                data[field] = max(0.0, min(10.0, float(data[field])))
            except (ValueError, TypeError):
                data[field] = 0.0

    return data


def _extract_from_text(content: str) -> Dict[str, Any]:
    """
    Fallback: Extract scores/feedback from raw text if JSON parse fails
    """
    extracted = _extract_useful_info_from_text(content)
    default_score = 5.0

    return {
        **{f: extracted.get(f, default_score) for f in SCORE_FIELDS},
        "general_feedback": extracted.get("general_feedback", "AI response parsing completed"),
        "detailed_feedback": content,
        "grammar_errors": extracted.get("grammar_errors", []),
        "grammar_improvements": extracted.get("grammar_improvements", []),
        "vocabulary_suggestions": extracted.get("vocabulary_suggestions", []),
        "vocabulary_improvements": extracted.get("vocabulary_improvements", []),
        "improvement_suggestions": extracted.get("improvement_suggestions", []),
        "suggested_writing": content
    }


def _extract_useful_info_from_text(text: str) -> Dict[str, Any]:
    """
    Use regex patterns to find scores and feedback in text
    """
    info = {}
    score_map = {
        "grammar": "grammar_score",
        "vocabulary": "vocabulary_score",
        "structure": "coherence_score",
        "content": "content_score",
        "overall": "overall_score",
        "coherence": "coherence_score"
    }

    # Regex tìm điểm
    for key, field_name in score_map.items():
        match = re.search(rf'{key}.*?(\d+\.?\d*)', text.lower())
        if match:
            info[field_name] = float(match.group(1))

    # Nếu thiếu overall_score thì tính trung bình
    if "overall_score" not in info:
        scores = [info.get(f, 5.0) for f in SCORE_FIELDS if f != "overall_score"]
        info["overall_score"] = round(sum(scores) / len(scores), 1)

    # Regex feedback
    general_feedback_match = re.search(r'(?:overall|general).*?(?:feedback|assessment|comment):\s*([^.]+)', text.lower())
    if general_feedback_match:
        info["general_feedback"] = general_feedback_match.group(1).strip()

    return info
