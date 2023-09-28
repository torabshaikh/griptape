from attr import define
from griptape.tokenizers import AnthropicTokenizer


@define(frozen=True)
class BedrockClaudeTokenizer(AnthropicTokenizer):
    DEFAULT_MODEL = 'anthropic.claude-v2'
