from typing import Optional
from .base import service, Maybe
from app.ext.templates.template import PromptTemplate
from app.service.types import TypeRequest, ModeRequest
from app.ext.providers import LLMManager


# example use 
# pt = PromptTemplate(
#     student_level="3.5", ## or 3.5-4.5, 4.0, 4.5-5.5 etc.
#     topic="Travel",
#     text="I like to travel by train...",
#     type=TypeRequest.PARAGRAPH,
#     mode=ModeRequest.WRITING,
# )
# prompt = pt.build()

# resp = await LLMManager().generate(prompt)

#@service