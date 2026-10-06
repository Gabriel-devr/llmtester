"""
Curador: liga as pecas da cura. Uso: `python -m core seu_script.py` ou `with Curador(...)`.

Em uma falha: lembrete (ja curado nesta execucao) -> alvo -> candidatos -> matcher
(aceita se nota x evidencia >= limiar e sem ambiguidade) -> LLM. Sem cura, o erro
original sobe. Ao sair do with, grava teste_curado.py de cada script com cura.
"""

from dataclasses import dataclass

from selenium.common.exceptions import NoSuchElementException

from core.alvo import acao_da_chamada, fingerprint_do_localizador
from core.dom_capture import capture_candidates, capture_fingerprint, seletor_candidatos
from core.interceptor import CallSite, FindFailure, Interceptor
from core.llm_client import LLMClient
from core.llm_healer import curar as curar_com_llm
from core.localizador import melhor_localizador
from core.matcher import evidencia, melhor_candidato
from core.script_curado import ResultadoScript, gerar_scripts_curados


@dataclass
class EventoDeCura:
    localizador: str
    metodo: str
    confianca: float | None
    antigo: tuple[str, str]
    novo: tuple[str, str] | None
    chamada: CallSite | None


class Curador:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        contexto: str | None = None,
        limiar_confianca: float = 0.6,
        gerar_script_curado: bool = True,
        verbose: bool = True,
    ):
        self.llm_client = llm_client
        self.contexto = contexto
        self.limiar_confianca = limiar_confianca
        self.gerar_script_curado = gerar_script_curado
        self.verbose = verbose
        self.eventos: list[EventoDeCura] = []
        self.script_curado: ResultadoScript | None = None
        self._interceptor: Interceptor | None = None
        self._curados: dict[tuple, tuple[str, str]] = {}

    def __enter__(self) -> "Curador":
        self._interceptor = Interceptor(on_failure=self._curar, verbose=self.verbose)
        self._interceptor.install()
        return self

    def __exit__(self, *exc_info) -> bool:
        self._interceptor.uninstall()
        if self.gerar_script_curado and self.eventos:
            try:
                self.script_curado = gerar_scripts_curados(self.eventos)
                for linha in self.script_curado.linhas():
                    self._log(linha)
            except Exception as erro:
                self._log(f"nao foi possivel gerar o script curado: {erro}")
        return False

    def relatorio(self) -> str:
        if not self.eventos:
            return "[curador] nenhuma cura foi necessaria."
        linhas = [f"[curador] {len(self.eventos)} cura(s):"]
        for i, e in enumerate(self.eventos, 1):
            nota = f" confianca={e.confianca:.2f}" if e.confianca is not None else ""
            novo = f" => {e.novo[0]}={e.novo[1]!r}" if e.novo else ""
            linhas.append(f"  {i}. {e.localizador} -> via '{e.metodo}'{nota}{novo}")
        return "\n".join(linhas)

    def _curar(self, alvo, falha: FindFailure, exc: Exception):
        driver = alvo if hasattr(alvo, "current_url") else alvo.parent

        elemento = self._curar_pelo_lembrete(driver, falha)
        if elemento is not None:
            return elemento

        esperado = fingerprint_do_localizador(falha.by, falha.value)
        candidatos = capture_candidates(driver, seletor_candidatos(esperado["tag"] if esperado else None))

        if esperado is not None:
            melhor = melhor_candidato(esperado, candidatos)
            if melhor is not None:
                confianca = melhor.pontuacao * evidencia(esperado)
                if confianca >= self.limiar_confianca and not melhor.ambigua:
                    return self._concluir(driver, falha, melhor.elemento, "similaridade", confianca)

        elemento = curar_com_llm(
            self.llm_client, self.contexto, falha.by, falha.value, acao_da_chamada(falha.call_site), candidatos,
        )
        if elemento is not None:
            return self._concluir(driver, falha, elemento, "llm", None)
        return None

    def _curar_pelo_lembrete(self, driver, falha: FindFailure):
        novo = self._curados.get((falha.url, falha.scope, falha.by, falha.value))
        if novo is None:
            return None
        try:
            return driver.find_element(*novo)
        except NoSuchElementException:
            return None

    def _concluir(self, driver, falha: FindFailure, elemento, metodo: str, confianca: float | None):
        novo = None
        try:
            novo = melhor_localizador(driver, elemento, capture_fingerprint(driver, elemento))
        except Exception as erro:
            self._log(f"nao foi possivel gerar um localizador novo: {erro}")
        if novo:
            self._curados[(falha.url, falha.scope, falha.by, falha.value)] = novo

        self.eventos.append(EventoDeCura(
            f"{falha.by}={falha.value!r}", metodo, confianca,
            (falha.by, falha.value), novo, falha.call_site,
        ))
        nota = f"{confianca:.2f}" if confianca is not None else "n/d"
        self._log(f"curado via '{metodo}' (confianca={nota})")
        return elemento

    def _log(self, msg) -> None:
        if self.verbose:
            print(f"  [curador] {msg}")
