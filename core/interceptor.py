"""
Desvia as chamadas a find_element do Selenium para que uma falha de
localizacao possa ser tratada sem alterar o codigo de teste.

Esperas explicitas (WebDriverWait): dentro de until(), um find_element
que falha e normal, o elemento pode so nao ter renderizado ainda. Por
isso a cura e adiada: so acontece se a espera estourar o timeout, e a
condicao e reavaliada uma vez com o elemento curado.
"""

import functools
import os
import sys
from dataclasses import dataclass
from typing import Callable, Optional

import selenium
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait

_SELENIUM_DIR = os.path.dirname(os.path.abspath(selenium.__file__))
_OWN_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class CallSite:
    file: str
    line: int
    function: str

    def __str__(self) -> str:
        return f"{os.path.basename(self.file)}:{self.line} em {self.function}()"


@dataclass(frozen=True)
class FindFailure:
    by: str
    value: str
    scope: str
    url: str
    call_site: Optional[CallSite]

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
        self._originais: dict = {}
        self._instalado = False
        self._dentro_do_handler = False
        self._esperas = 0
        self._esperas_negativas = 0
        self._pendentes: dict = {}
        self._redirecionados: dict = {}

    def install(self) -> "Interceptor":
        if self._instalado:
            raise RuntimeError("Interceptor ja esta instalado.")
        self._originais[WebDriver] = WebDriver.find_element
        self._originais[WebElement] = WebElement.find_element
        self._originais[(WebDriverWait, "until")] = WebDriverWait.until
        self._originais[(WebDriverWait, "until_not")] = WebDriverWait.until_not
        WebDriver.find_element = self._envolver(WebDriver.find_element, "driver")
        WebElement.find_element = self._envolver(WebElement.find_element, "element")
        WebDriverWait.until = self._envolver_espera(WebDriverWait.until, negativa=False)
        WebDriverWait.until_not = self._envolver_espera(WebDriverWait.until_not, negativa=True)
        self._instalado = True
        return self

    def uninstall(self) -> None:
        if not self._instalado:
            return
        WebDriver.find_element = self._originais[WebDriver]
        WebElement.find_element = self._originais[WebElement]
        WebDriverWait.until = self._originais[(WebDriverWait, "until")]
        WebDriverWait.until_not = self._originais[(WebDriverWait, "until_not")]
        self._originais.clear()
        self._instalado = False

    def _envolver(self, original, scope: str):
        interceptor = self

        @functools.wraps(original)
        def patched(alvo, by=By.ID, value=None):
            chave = (scope, str(by), str(value))
            redirecionado = interceptor._redirecionados.get(chave)
            if redirecionado is not None:
                return redirecionado
            try:
                elemento = original(alvo, by, value)
            except NoSuchElementException as exc:
                if interceptor._dentro_do_handler or interceptor._esperas_negativas:
                    raise
                if interceptor._esperas:
                    interceptor._pendentes[chave] = (alvo, by, value)
                    raise
                curado = interceptor._tentar_curar(alvo, by, value, scope, exc)
                if curado is not None:
                    return curado
                raise
            interceptor._pendentes.pop(chave, None)
            return elemento

        return patched

    def _envolver_espera(self, original, negativa: bool):
        interceptor = self

        @functools.wraps(original)
        def patched(espera, method, message=""):
            if negativa:
                interceptor._esperas_negativas += 1
                try:
                    return original(espera, method, message)
                finally:
                    interceptor._esperas_negativas -= 1

            externa = interceptor._esperas == 0
            if externa:
                interceptor._pendentes = {}
            try:
                interceptor._esperas += 1
                try:
                    return original(espera, method, message)
                finally:
                    interceptor._esperas -= 1
            except TimeoutException as exc:
                if not externa:
                    raise
                return interceptor._curar_espera(espera, method, exc)

        return patched

    def _tentar_curar(self, alvo, by, value, scope: str, exc: Exception):
        falha = self._registrar(alvo, by, value, scope)
        if self.on_failure is None:
            return None
        self._dentro_do_handler = True
        try:
            return self.on_failure(alvo, falha, exc)
        finally:
            self._dentro_do_handler = False

    def _curar_espera(self, espera, method, exc: TimeoutException):
        pendentes, self._pendentes = list(self._pendentes.items()), {}
        if not pendentes or self.on_failure is None:
            raise exc

        curados = {}
        for (scope, by, value), (alvo, _, _) in pendentes:
            curado = self._tentar_curar(alvo, by, value, scope, exc)
            if curado is not None:
                curados[(scope, by, value)] = curado
        if not curados:
            raise exc

        self._redirecionados = curados
        try:
            resultado = method(espera._driver)
        except NoSuchElementException:
            resultado = None
        finally:
            self._redirecionados = {}
        if resultado:
            return resultado
        raise exc

    def _registrar(self, alvo, by, value, scope: str) -> FindFailure:
        driver = alvo if isinstance(alvo, WebDriver) else alvo.parent
        try:
            url = driver.current_url
        except Exception:
            url = "<indisponivel>"

        falha = FindFailure(str(by), str(value), scope, url, _find_call_site())
        if self.verbose:
            print(f"[interceptor] falha: {falha}")
        return falha
