from abc import ABC, abstractmethod


class IAudioPort(ABC):
    """Abstract audio port for transcription and text-to-speech."""

    @abstractmethod
    def transcribe_audio(self, audio_uri: str) -> str:
        """Transcribe an audio asset and return the decoded text."""
        raise NotImplementedError

    @abstractmethod
    def transcribe_audio_bytes(self, audio_bytes: bytes, media_format: str = "webm") -> str:
        """Upload raw audio to S3 (when configured) and transcribe via Amazon Transcribe."""
        raise NotImplementedError

    @abstractmethod
    def synthesize_speech(
        self,
        text: str,
        voice_id: str = "Joanna",
        output_format: str = "mp3",
        force: bool = False,
    ) -> bytes:
        """Synthesize speech from text and return raw audio bytes."""
        raise NotImplementedError
