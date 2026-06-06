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
        audio_url: optional URL where the recorded audio is stored. When set, the app can transcribe this audio and optionally return synthesized speech.
    """

    industry: str
    query: str
    audio_url: Optional[str] = None

