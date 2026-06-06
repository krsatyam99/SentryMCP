from abc import ABC, abstractmethod


class IAudioPort(ABC):
    """Abstract audio port for transcription and text-to-speech."""

    @abstractmethod
    def transcribe_audio(self, audio_uri: str) -> str:
        """Transcribe an audio asset and return the decoded text."""
        raise NotImplementedError

    @abstractmethod
    def synthesize_speech(self, text: str, voice_id: str = "Joanna", output_format: str = "mp3") -> bytes:
        """Synthesize speech from text and return raw audio bytes."""
        raise NotImplementedError
