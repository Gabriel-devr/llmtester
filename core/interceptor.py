"""
O Interceptor vai desviar as chamadas a "find_element" para que uma falha de localização possa ser observada e, no futuro, tratada sem que o códgio de teste precise ser alterado
"""

"""
O Interceptor não decide quando curar, não lê os snapshots, não calcula similaridade. Ele apenas oferece o ponto de entrada.
"""

import functools
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

import selenium
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

_SELENIUM_DIR = os.path.dirname(os.path.abspath(selenium.__file__))
_OWN_DIR = os.path.dirname(os.path.abspath(__file__))

@dataclass(frozen=True)
class CallSite:
    file: str
    line: int
    function: str

    def __str__ (self) -> str:
        return f"{os.path.basename(self.file)}:{self.line} em {self.function}()"

@dataclass(frozen=True)
class FindFailure:
    by: str
    value: str
    scope: str
    url: str
    call_site: Optional[CallSite]
    at: str

    def __str__(self) -> str:
        origem = self.call_site or "origem desconhecida"
        return f"[{self.by}={self.value!r}] escopo={self.scope} <- {origem}"

def _find_call_site() -> Optional[CallSite]:
    frame = sys._getframe(1)
    while frame is not None:
        arquivo = os.path.abspath(frame.f_code.co_filename)
        if not arquivo.startswith(_SELENIUM_DIR) and not arquivo.startswith(_OWN_DIR):
            return CallSite(arquivo, frame.f_lineno, frame.f_code.co_name)
        frame = frame.f_back
    return None

class Interceptor:
    def __init__(
        self,
        on_failure: Optional[Callable[[object, FindFailure, Exception], Optional[WebElement]]] = None,
        verbose: bool = True,
    ):
        self.on_failure = on_failure
        self.verbose = verbose
        self.failures: list[FindFailure] = []
        self._originais: dict = {}
        self._instalado = False
        self._dentro_do_handler = False

    def install(self) -> "Interceptor":
        if self._instalado:
            raise RuntimeError("Interceptor já está instalado.")
        self._originais[WebDriver] = WebDriver.find_element
        self._originais[WebElement] = WebElement.find_element
        WebDriver.find_element = self._envolver(WebDriver.find_element, "driver")
        WebElement.find_element = self._envolver(WebElement.find_element, "element")
        self._instalado = True
        return self

    def uninstall(self) -> None:
        if not self._instalado:
            return
        WebDriver.find_element = self._originais[WebDriver]
        WebElement.find_element = self._originais[WebElement]
        self._originais.clear()
        self._instalado = False

    # o desvio

    def _envolver(self, original, scope: str):
        interceptor = self

        @functools.wraps(original)
        def patched(alvo, by=By.ID, value=None):
            try:
                return original(alvo, by, value)
            except NoSuchElementException as exc:
                if interceptor._dentro_do_handler:
                    raise
                falha = interceptor._registrar(alvo, by, value, scope)
                if interceptor.on_failure is None:
                    raise
                interceptor._dentro_do_handler = True
                try:
                    curado = interceptor.on_failure(alvo, falha, exc)
                finally:
                    interceptor._dentro_do_handler = False
                if curado is not None:
                    return curado
                raise

        return patched

    # registro 

    def _registrar(self, alvo, by, value, scope: str) -> FindFailure:
        driver = alvo if isinstance(alvo, WebDriver) else alvo.parent
        try:
            url = driver.current_url
        except Exception:
            url = "<indisponível>"

        falha = FindFailure(
            by=str(by),
            value=str(value),
            scope=scope,
            url=url,
            call_site=_find_call_site(),
            at=datetime.now(timezone.utc).isoformat(),
        )
        self.failures.append(falha)
        if self.verbose:
            print(f"[interceptor] falha #{len(self.failures)}: {falha}")
        return falha

    # relatório

    def summary(self) -> str:
        if not self.failures:
            return "[interceptor] nenhuma falha de localização."
        linhas = [f"[interceptor] {len(self.failures)} falha(s):"]
        linhas += [f"  {i}. {f}" for i, f in enumerate(self.failures, 1)]
        return "\n".join(linhas)


@contextmanager
def intercepting(on_failure=None, verbose: bool = True):
    """Instala o desvio durante o bloco e o remove ao sair, mesmo em exceção."""
    interceptor = Interceptor(on_failure=on_failure, verbose=verbose)
    interceptor.install()
    try:
        yield interceptor
    finally:
        interceptor.uninstall()
        