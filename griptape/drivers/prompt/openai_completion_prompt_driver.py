import os
from typing import Optional, Iterator
import openai
from attr import define, field, Factory
from griptape.artifacts import TextArtifact
from griptape.utils import PromptStack
from griptape.drivers import BasePromptDriver
from griptape.tokenizers import OpenAiTokenizer
from griptape.events import CompletionChunkEvent
from typing import Tuple, Type


@define
class OpenAiCompletionPromptDriver(BasePromptDriver):
    """
    Attributes:
        api_type: Can be changed to use OpenAI models on Azure.
        api_version: API version.
        api_base: API URL.
        api_key: API key to pass directly; by default uses `OPENAI_API_KEY` environment variable.
        max_tokens: Optional maximum return tokens. If not specified, the value will be automatically generated based by the tokenizer.
        model: OpenAI model name. Uses `gpt-4` by default.
        organization: OpenAI organization.
        tokenizer: Custom `OpenAiTokenizer`.
        user: OpenAI user.
    """

    api_type: str = field(default=openai.api_type, kw_only=True)
    api_version: Optional[str] = field(default=openai.api_version, kw_only=True)
    api_base: str = field(default=openai.api_base, kw_only=True)
    api_key: Optional[str] = field(
        default=Factory(lambda: os.environ.get("OPENAI_API_KEY")), kw_only=True
    )
    organization: Optional[str] = field(
        default=openai.organization, kw_only=True
    )
    model: str = field(kw_only=True)
    tokenizer: OpenAiTokenizer = field(
        default=Factory(
            lambda self: OpenAiTokenizer(model=self.model), takes_self=True
        ),
        kw_only=True,
    )
    user: str = field(default="", kw_only=True)
    ignored_exception_types: Tuple[Type[Exception], ...] = field(
        default=Factory(lambda: (openai.InvalidRequestError)), kw_only=True
    )

    def try_run(self, prompt_stack: PromptStack) -> TextArtifact:
        result = openai.Completion.create(**self._base_params(prompt_stack))

        if len(result.choices) == 1:
            return TextArtifact(value=result.choices[0].text.strip())
        else:
            raise Exception(
                "completion with more than one choice is not supported yet"
            )

    def try_stream(self, prompt_stack: PromptStack) -> Iterator[TextArtifact]:
        result = openai.Completion.create(
            **self._base_params(prompt_stack), stream=True
        )

        for chunk in result:
            if len(chunk.choices) == 1:
                choice = chunk.choices[0]
                delta_content = choice["text"]
                yield TextArtifact(value=delta_content)

            else:
                raise Exception(
                    "completion with more than one choice is not supported yet"
                )

    def _base_params(self, prompt_stack: PromptStack) -> dict:
        prompt = self.prompt_stack_to_string(prompt_stack)

        return {
            "model": self.model,
            "max_tokens": self.max_output_tokens(prompt),
            "temperature": self.temperature,
            "stop": self.tokenizer.stop_sequences,
            "user": self.user,
            "api_key": self.api_key,
            "organization": self.organization,
            "api_version": self.api_version,
            "api_base": self.api_base,
            "api_type": self.api_type,
            "prompt": prompt,
        }
