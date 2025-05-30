from unittest.mock import Mock, mock_open, patch

import pytest

from griptape.artifacts import AudioArtifact
from griptape.tools.audio_transcription.tool import AudioTranscriptionTool


class TestTranscriptionTool:
    @pytest.fixture()
    def audio_transcription_driver(self) -> Mock:
        return Mock()

    @pytest.fixture()
    def audio_loader(self) -> Mock:
        loader = Mock()
        loader.load.return_value = AudioArtifact(value=b"audio data", format="wav")

        return loader

    @pytest.fixture(
        autouse=True,
    )
    def mock_path(self, mocker) -> Mock:
        mocker.patch("pathlib.Path.read_bytes", return_value=b"transcription")

        return mocker

    def test_init_transcription_client(self, audio_transcription_driver, audio_loader) -> None:
        assert AudioTranscriptionTool(audio_transcription_driver=audio_transcription_driver, audio_loader=audio_loader)

    @patch("builtins.open", mock_open(read_data=b"audio data"))
    def test_transcribe_audio_from_disk(self, audio_transcription_driver, audio_loader) -> None:
        client = AudioTranscriptionTool(
            audio_transcription_driver=audio_transcription_driver, audio_loader=audio_loader
        )
        client.audio_transcription_driver.run.return_value = Mock(value="transcription")  # pyright: ignore[reportFunctionMemberAccess]

        text_artifact = client.transcribe_audio_from_disk(params={"values": {"path": "audio.wav"}})

        assert text_artifact
        assert text_artifact.value == "transcription"

    def test_transcribe_audio_from_memory(self, audio_transcription_driver, audio_loader) -> None:
        client = AudioTranscriptionTool(
            audio_transcription_driver=audio_transcription_driver, audio_loader=audio_loader
        )
        memory = Mock()
        memory.load_artifacts = Mock(return_value=[AudioArtifact(value=b"audio data", format="wav", name="name")])
        client.find_input_memory = Mock(return_value=memory)

        client.audio_transcription_driver.run.return_value = Mock(value="transcription")  # pyright: ignore[reportFunctionMemberAccess]

        text_artifact = client.transcribe_audio_from_memory(
            params={"values": {"memory_name": "memory", "artifact_namespace": "namespace", "artifact_name": "name"}}
        )

        assert text_artifact
        assert text_artifact.value == "transcription"
