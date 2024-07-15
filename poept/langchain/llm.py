import re
import tempfile

from langchain.llms.base import LLM
from typing import Optional, List, Any
from langchain_core.pydantic_v1 import Field

from ..poept import PoePT

# [CustomLLM](https://python.langchain.com/v0.1/docs/modules/model_io/llms/custom_llm/)
# Inspired by https://github.com/langchain-ai/langchain/blob/master/libs/community/langchain_community/llms/openai.py#L145

_poe : Optional[PoePT] = None

def _get_files(text: str):
    # Define the regex pattern to find text within <<< >>>
    pattern = r'<<<(.*?)>>>'

    # Find all matches of the pattern
    extracted_content = re.findall(pattern, text, re.DOTALL)

    # Remove the <<< >>> sections from the original text
    cleaned_text = re.sub(pattern, '', text, flags=re.DOTALL)

    return cleaned_text, extracted_content

def _ask(prompt: str, model: str, email=None):
    global _poe
    if _poe is None:
        _poe = PoePT(email=email)

    text, snippets = _get_files(prompt)
    files = []

    for content in snippets:
        f = tempfile.NamedTemporaryFile("w", suffix='.txt', encoding='utf8')
        f.write(content)
        f.flush()
        _poe.attach(f.name, bot=model)
        files.append(f)

    try:
        return _poe.ask(text, bot=model)
    finally:
        for f in files:
            f.close()

class PoeLLM(LLM):
    model: str = Field(default="Assistant")
    email: Optional[str] = Field(default=None)
    cookies: Optional[list] = Field(default=[])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Takes in a string and some optional stop words, and returns a string. Used by invoke.
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        """Call out to Poe's ask method.

        Args:
            prompt: The prompt to pass into the model.
            stop: Optional list of stop words to use when generating.

        Returns:
            The string generated by the model.
        """
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")

        return _ask(prompt, model=self.model, email=self.email)

    # A property that returns a string, used for logging purposes only.
    @property
    def _llm_type(self) -> str:
        return "Poe"