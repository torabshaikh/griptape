from __future__ import annotations

from attrs import define

from .base_text_to_speech_event import BaseTextToSpeechEvent
from .base_image_generation_event import BaseImageGenerationEvent


@define
class FinishTextToSpeechEvent(BaseTextToSpeechEvent):
    ...
