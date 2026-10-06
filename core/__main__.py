"""Uso: python -m core meu_script.py (grava meu_script_curado.py ao lado do original)."""

import argparse
import os
import runpy
import sys
from pathlib import Path

from core.curador import Curador


def _escolher_llm(nome: str | None):
    if nome is None:
        nome = "groq" if os.environ.get("GROQ_API_KEY") else "gemini" if os.environ.get("GEMINI_API_KEY") else None
    if nome == "groq":
        from core.adapters.groq_adapter import groq_client
        return groq_client()
    if nome == "gemini":
        from core.adapters.gemini_adapter import gemini_client
        return gemini_client()
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m core",
        description="Roda um script Selenium sob o Curador e gera uma copia corrigida (*_curado.py).",
    )
    parser.add_argument("script", help="o arquivo .py da automacao")
    parser.add_argument("--contexto", help="uma frase sobre o que a automacao faz (ajuda a LLM)")
    parser.add_argument("--llm", choices=["groq", "gemini"], help="padrao: a que tiver chave no ambiente")
    parser.add_argument("--limiar", type=float, default=0.6, help="confianca minima para dispensar a LLM (padrao 0.6)")
    parser.add_argument("--sem-script-curado", action="store_true", help="nao gerar o arquivo *_curado.py")
    parser.add_argument("argumentos", nargs=argparse.REMAINDER, help="argumentos repassados ao script")
    ns = parser.parse_args()

    script = Path(ns.script).resolve()
    if not script.is_file():
        sys.exit(f"Arquivo nao encontrado: {script}")

    sys.argv = [str(script), *ns.argumentos]
    sys.path.insert(0, str(script.parent))

    curador = Curador(
        llm_client=_escolher_llm(ns.llm),
        contexto=ns.contexto,
        limiar_confianca=ns.limiar,
        gerar_script_curado=not ns.sem_script_curado,
    )
    try:
        with curador:
            runpy.run_path(str(script), run_name="__main__")
    finally:
        print(curador.relatorio())


if __name__ == "__main__":
    main()
