import pytest
from unittest import mock
from griptape.tokenizers import BedrockJurassicTokenizer


class TestBedrockJurassicTokenizer:
    @pytest.fixture(autouse=True)
    def mock_session(self, mocker):
        fake_tokenization = '{"prompt": {"tokens": [{}, {}, {}]}}'
        mock_session_class = mocker.patch("boto3.Session")

        mock_session_object = mock.Mock()
        mock_client = mock.Mock()
        mock_response = mock.Mock()

        mock_response.get().read.return_value = fake_tokenization
        mock_client.invoke_model.return_value = mock_response
        mock_session_object.client.return_value = mock_client
        mock_session_class.return_value = mock_session_object

    def test_unsupported_methods(self):
        with pytest.raises(NotImplementedError):
            BedrockJurassicTokenizer(
                model=BedrockJurassicTokenizer.DEFAULT_MODEL
            ).encode("foo bar")

        with pytest.raises(NotImplementedError):
            BedrockJurassicTokenizer(
                model=BedrockJurassicTokenizer.DEFAULT_MODEL
            ).decode([1, 2, 3])

    def test_titan_tokens_left(self):
        assert (
            BedrockJurassicTokenizer(
                model=BedrockJurassicTokenizer.DEFAULT_MODEL
            ).tokens_left("foo bar")
            == 8189
        )
