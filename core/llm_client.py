"""Contrato de uma LLM: funcao que recebe o prompt (texto) e devolve a resposta (texto)."""

from typing import Callable

LLMClient = Callable[[str], str]
