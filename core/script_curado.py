"""
Gera uma copia do script de teste com os localizadores curados, sem
alterar o original (teste.py -> teste_curado.py).
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from selenium.webdriver.common.by import By

_NOME_DO_BY = {v: k for k, v in vars(By).items() if k.isupper() and isinstance(v, str)}


@dataclass
class ResultadoScript:
    gerados: dict = field(default_factory=dict)
    pendentes: list = field(default_factory=list)

    def linhas(self) -> list[str]:
        saida = [f"script curado: {caminho} ({n} localizador(es) trocado(s))"
                 for caminho, n in self.gerados.items()]
        for evento, motivo in self.pendentes:
            onde = evento.chamada or "origem desconhecida"
            saida.append(f"aplicar manualmente ({motivo}): {evento.localizador} em {onde}")
        return saida


def _padrao(antigo: tuple[str, str]):
    nome = _NOME_DO_BY[antigo[0]]
    return re.compile(r"By\.%s(?P<sep>\s*,\s*)(?P<q>[\"'])%s(?P=q)" % (nome, re.escape(antigo[1])))


def _literal(valor: str, preferida: str) -> str | None:
    outra = '"' if preferida == "'" else "'"
    for q in (preferida, outra):
        if q not in valor and "\\" not in valor and "\n" not in valor:
            return f"{q}{valor}{q}"
    return None


def _trocar(linhas: list[str], evento) -> str | None:
    if evento.novo is None:
        return "sem localizador estavel para o elemento"
    if evento.antigo[0] not in _NOME_DO_BY or evento.novo[0] not in _NOME_DO_BY:
        return "tipo de localizador desconhecido"

    padrao = _padrao(evento.antigo)
    inicio = evento.chamada.line - 1
    alvos = [i for i in range(max(0, inicio), min(len(linhas), inicio + 4)) if padrao.search(linhas[i])]
    if not alvos:
        alvos = [i for i, linha in enumerate(linhas) if padrao.search(linha)]
    if not alvos:
        return "localizador nao esta escrito como literal"
    if len(alvos) > 1 or len(padrao.findall(linhas[alvos[0]])) > 1:
        return "localizador aparece mais de uma vez"

    i = alvos[0]
    achado = padrao.search(linhas[i])
    literal = _literal(evento.novo[1], achado.group("q"))
    if literal is None:
        return "valor novo tem aspas ou barras"
    novo = f"By.{_NOME_DO_BY[evento.novo[0]]}{achado.group('sep')}{literal}"
    linhas[i] = linhas[i][:achado.start()] + novo + linhas[i][achado.end():]
    return None


def gerar_scripts_curados(eventos) -> ResultadoScript:
    resultado = ResultadoScript()
    por_arquivo: dict[Path, dict] = {}
    for evento in eventos:
        if evento.chamada is None:
            resultado.pendentes.append((evento, "origem da chamada desconhecida"))
            continue
        por_arquivo.setdefault(Path(evento.chamada.file), {})[(evento.antigo, evento.novo)] = evento

    for origem, unicos in por_arquivo.items():
        if origem.suffix != ".py" or not origem.is_file():
            resultado.pendentes += [(e, "arquivo de origem indisponivel") for e in unicos.values()]
            continue
        linhas = origem.read_bytes().decode("utf-8").splitlines(keepends=True)
        trocas = 0
        for evento in unicos.values():
            motivo = _trocar(linhas, evento)
            if motivo:
                resultado.pendentes.append((evento, motivo))
            else:
                trocas += 1
        if trocas:
            destino = origem.with_name(f"{origem.stem}_curado{origem.suffix}")
            destino.write_bytes("".join(linhas).encode("utf-8"))
            resultado.gerados[destino] = trocas
    return resultado
