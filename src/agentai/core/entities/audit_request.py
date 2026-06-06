"""Core domain entity: AuditRequest

This simple dataclass represents the input to the analysis use case.
Keep it minimal for the POC so it is easy to reason about and test.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AuditRequest:
    """Represents a voice-audit request.

    Attributes:
        industry: target industry track (e.g., 'fintech', 'health').
        query: a short natural-language query describing what to audit.
        audio_url: optional S3 URI (s3://bucket/key) for Amazon Transcribe.
        audio_base64: optional raw microphone audio (base64) uploaded to S3 then transcribed.
        audio_media_format: file extension/format for audio_base64 (e.g. webm, wav).
    """

    industry: str
    query: str = ""
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None
    audio_media_format: Optional[str] = "webm"

