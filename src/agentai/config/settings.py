"""Simple configuration loader for environment-driven settings.

This module centralizes configuration access for the POC. It intentionally
keeps behavior minimal and documented so interviewers can follow easily.
"""
import os
from typing import Optional

from dotenv import load_dotenv

# Load environment configuration from .env when available.
# This allows local development to keep AWS and Bedrock settings outside
# of source code while still supporting standard environment variables.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))


def get_setting(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return the environment value for `name` or `default` if not set."""
    return os.getenv(name, default)

