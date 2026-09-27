"""
O snapshot repo irá gravar e ler os snapshots como arquivos JSON. Só transforma dict em arquivo.
"""

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

from core.dom_capture import SCHEMA_VERSION

_NOME_INVALIDO = set('/||:*?"<>|')

def page_key(url:str) -> str:
    #transforma a url em uma chave de arquivo válida
    partes = urlparse(url)
    if partes.scheme == "file":
        return Path(unquote(partes.path)).stem
    caminho = partes.path.strip("/").replace("/", "_") or "index" 
    #Transforma o caminho em um nome para o arquivo, caso seja uma url sem caminho, o path será vazio e ficaremos com o "index"
    return f"{partes.netloc}_{caminho}".replace(":","_")

class SnapshotRepository:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    #caminhos

    def path_for(self, name: str) -> Path:
        if not name or _NOME_INVALIDO & set(name) or name in (".",".."):
            raise ValueError(f'Nome de snapshot invalido: {name!r}') #caracteres que sao proibidos em arquivos windows
        return self.base_dir / f"{name}.json" #vem do page_key(url)

    def list_names(self)-> list[str]:
        return sorted(p.stem for p in self.base_dir.glob("*.json"))

    #escrita

    def save(self, snapshot: dict, name: str | None = None) -> Path:
        #escre o conteudo em um arquivo temporario na pasta
        name = name or page_key(snapshot["source"])
        destino = self.path_for(name)
        conteudo = json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True)

        temporario = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=self.base_dir,prefix=f'.{name}.', suffix='.tmp', delete=False,
            ) as arquivo:
                temporario = Path(arquivo.name)
                arquivo.write(conteudo)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, destino)
            temporario= None
            return destino
        finally:
            if temporario is not None and temporario.exists():
                temporario.unlink()

    #leitura
    def load(self, name:str) -> dict:
        caminho = self.path_for(name)
        if not caminho.exists():
            raise FileNotFoundError(
                f"Baseline {name!r} nao existe em {self.base_dir}."
                f"Disponiveis: {self.list_names() or 'nenhum'}"
            )

        dados = json.loads(caminho.read_text(encoding="utf-8"))
        versao = dados.get("schema_version")
        if versao != SCHEMA_VERSION:
            raise ValueError(
                f"{caminho.name} foi gravado no schema v{versao}, "
                f"o codigo espera v{SCHEMA_VERSION}. Recapture o baseline"
            )
        return dados

    def load_for_url(self, url:str) -> dict:
        return self.load(page_key(url))