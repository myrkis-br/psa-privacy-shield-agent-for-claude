"""
PSA - Privacy Shield Agent
Script: anonymize_html.py
Responsável: PSA Guardião

Anonimiza documentos HTML:
  - Preserva toda a estrutura HTML (tags, atributos, CSS, JS)
  - Anonimiza apenas o conteúdo textual entre tags usando text_engine
  - Detecta CPF, CNPJ, email, telefone, CEP, datas, valores, nomes
  - Salva como HTML anonimizado em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_html.py <caminho_do_arquivo> [--sample <n>]

Exemplos:
  python3 scripts/anonymize_html.py data/real/relatorio.html
"""

import sys
import json
import argparse
import logging
import re
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Configuração de caminhos
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANONYMIZED_DIR = BASE_DIR / "data" / "anonymized"
MAPS_DIR = BASE_DIR / "data" / "maps"
LOGS_DIR = BASE_DIR / "logs"

for d in (ANONYMIZED_DIR, MAPS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR / "scripts"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA-Guardião] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

from text_engine import TextAnonymizer


# ---------------------------------------------------------------------------
# Parser HTML que reconstrói o documento anonimizando apenas texto
# ---------------------------------------------------------------------------

class _AnonymizingHTMLParser(HTMLParser):
    """
    Parser HTML que reconstrói o documento inteiro,
    aplicando text_engine apenas ao conteúdo textual.
    """

    # Tags cujo conteúdo NÃO deve ser anonimizado
    SKIP_TAGS = {"script", "style", "code", "pre"}

    def __init__(self, engine: TextAnonymizer):
        super().__init__(convert_charrefs=False)
        self.engine = engine
        self.output = []  # type: List[str]
        self._skip_stack = []  # type: List[str]

    def handle_decl(self, decl: str):
        self.output.append(f"<!{decl}>")

    def handle_pi(self, data: str):
        self.output.append(f"<?{data}>")

    def handle_starttag(self, tag: str, attrs: list):
        if tag.lower() in self.SKIP_TAGS:
            self._skip_stack.append(tag.lower())

        attr_str = ""
        for name, value in attrs:
            if value is None:
                attr_str += f" {name}"
            else:
                # Anonimiza atributos que podem conter PII
                if name.lower() in ("title", "alt", "placeholder", "value", "content"):
                    if not self._skip_stack:
                        value = self.engine.anonymize(value)
                attr_str += f' {name}="{value}"'

        self.output.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str):
        if self._skip_stack and self._skip_stack[-1] == tag.lower():
            self._skip_stack.pop()
        self.output.append(f"</{tag}>")

    def handle_startendtag(self, tag: str, attrs: list):
        attr_str = ""
        for name, value in attrs:
            if value is None:
                attr_str += f" {name}"
            else:
                attr_str += f' {name}="{value}"'
        self.output.append(f"<{tag}{attr_str}/>")

    def handle_data(self, data: str):
        if self._skip_stack:
            # Dentro de <script>, <style>, etc. — não anonimizar
            self.output.append(data)
        else:
            # Texto visível — anonimizar
            if data.strip():
                self.output.append(self.engine.anonymize(data))
            else:
                self.output.append(data)

    def handle_entityref(self, name: str):
        self.output.append(f"&{name};")

    def handle_charref(self, name: str):
        self.output.append(f"&#{name};")

    def handle_comment(self, data: str):
        # Anonimiza comentários HTML (podem conter PII)
        anon = self.engine.anonymize(data)
        self.output.append(f"<!--{anon}-->")

    def get_result(self) -> str:
        return "".join(self.output)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_html(
    input_path: Path,
    sample_paragraphs: int = 20,
) -> Tuple[Path, Path]:
    """
    Anonimiza um documento HTML preservando a estrutura.

    Args:
        input_path: Caminho para o arquivo .html/.htm
        sample_paragraphs: não usado (HTML é processado inteiro)

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    suffix = input_path.suffix.lower()

    log.info(f"Iniciando anonimização HTML: {input_path.name}")

    # --- Leitura com fallback de encoding ---
    content = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            content = input_path.read_text(encoding=enc)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        content = input_path.read_text(encoding="utf-8", errors="replace")
        log.warning("Encoding não detectado, usando UTF-8 com replace")

    log.info(f"HTML carregado: {len(content)} caracteres")

    # --- Anonimização ---
    engine = TextAnonymizer()
    parser = _AnonymizingHTMLParser(engine)
    parser.feed(content)
    anonymized_html = parser.get_result()

    log.info(f"Entidades substituídas: {len(engine.entity_map)} ocorrências únicas")

    for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
        log.info(f"  Substituição #{i+1}: -> '{token}'")

    # --- Salvar arquivo anonimizado ---
    anon_filename = f"anon_{stem}_{timestamp}{suffix}"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(anonymized_html, encoding="utf-8")
    log.info(f"HTML anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "documento",
        "formato_original": suffix,
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_caracteres_original": len(content),
        "total_caracteres_anonimizado": len(anonymized_html),
        "entidades": {
            token: original
            for token, original in engine.entity_map.items()
        },
        "estatisticas": {
            "pessoas_substituidas": engine._counters["pessoa"],
            "empresas_substituidas": engine._counters["empresa"],
            "total_entidades": len(engine.entity_map),
        },
    }

    map_filename = f"map_{stem}_{timestamp}.json"
    map_path = MAPS_DIR / map_filename
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa salvo: {map_path}")
    log.info(
        f"Anonimização concluída: {engine._counters['pessoa']} pessoas, "
        f"{engine._counters['empresa']} empresas substituídas."
    )

    return anon_path, map_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Anonimizador de documentos HTML"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo HTML a anonimizar")
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    anon_path, map_path = anonymize_html(input_path)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
