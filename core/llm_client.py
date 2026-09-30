"""
É um callable que recebe um prompt do que a LLM precisa cumprir
"""

from typing import Callable

LLMClient = Callable[[str], str]
