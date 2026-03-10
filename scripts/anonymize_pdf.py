"""
PSA - Privacy Shield Agent
Script: anonymize_pdf.py
Responsável: PSA Guardião

Anonimiza PDFs:
  - Usa pdfplumber para extrair texto de cada página
  - Detecta e substitui CPF, CNPJ, email, telefone, CEP, datas, valores monetários
  - Substitui nomes por tokens [PESSOA_N] / [EMPRESA_N]
  - M-10: Default 10 páginas (mais representativo que 3)
  - M-11: Loga erros de tabelas em vez de silenciar
  - M-12: Avisa sobre PDFs escaneados (sem texto)
  - Salva como TXT anonimizado em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_pdf.py <caminho_do_arquivo> [--pages <n_paginas>]

Exemplos:
  python3 scripts/anonymize_pdf.py data/real/contrato.pdf
  python3 scripts/anonymize_pdf.py data/real/relatorio.pdf --pages 5
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

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

# ---------------------------------------------------------------------------
# Imports de terceiros
# ---------------------------------------------------------------------------

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from text_engine import TextAnonymizer

# ---------------------------------------------------------------------------
# Extração de texto por página
# ---------------------------------------------------------------------------

def _extract_pages(path: Path) -> List[Dict]:
    """
    Extrai texto de cada página do PDF.
    Retorna lista de dicts: {page_num, text, has_tables, word_count}
    """
    if pdfplumber is None:
        raise ImportError("pdfplumber não instalado. Execute: pip3 install pdfplumber")

    pages = []
    empty_pages = 0

    with pdfplumber.open(str(path)) as pdf:
        total_pages = len(pdf.pages)
        log.info(f"PDF aberto: {total_pages} páginas")

        for i, page in enumerate(pdf.pages, start=1):
            # Extrai texto corrido
            text = page.extract_text() or ""

            # Extrai tabelas e converte para texto tabular
            table_texts = []
            try:
                tables = page.extract_tables()
                for table in (tables or []):
                    for row in table:
                        if row:
                            row_str = " | ".join(
                                str(cell).strip() if cell else ""
                                for cell in row
                            )
                            if row_str.strip(" |"):
                                table_texts.append(row_str)
            except Exception as e:
                # M-11: Loga erro de tabela em vez de silenciar
                log.warning(f"  Erro ao extrair tabelas da página {i}: {e}")

            full_text = text
            if table_texts:
                full_text += "\n\n[TABELA]\n" + "\n".join(table_texts)

            word_count = len(full_text.split())

            if not full_text.strip():
                empty_pages += 1

            pages.append({
                "page_num": i,
                "text": full_text.strip(),
                "has_tables": bool(table_texts),
                "word_count": word_count,
            })

    # M-12: Aviso sobre PDFs escaneados
    if empty_pages > 0:
        pct_empty = empty_pages / len(pages) * 100 if pages else 0
        if pct_empty > 50:
            log.warning(
                f"  AVISO: {empty_pages}/{len(pages)} páginas sem texto ({pct_empty:.0f}%). "
                "Este PDF pode ser escaneado (imagem). "
                "O PSA não consegue extrair texto de PDFs baseados em imagem — "
                "considere usar OCR antes de anonimizar."
            )
        elif empty_pages > 0:
            log.info(f"  {empty_pages} página(s) sem texto extraível.")

    return pages


def _sample_pages(pages: List[Dict], max_pages: int) -> List[Dict]:
    """
    Seleciona amostra de páginas.

    Estratégia:
    - Sempre inclui a página 1 (sumário executivo / capa / introdução)
    - Prefere páginas com mais conteúdo (word_count alto)
    - Para documentos com índice na pág. 2, inclui ela
    - Distribui seleção ao longo do documento
    """
    if len(pages) <= max_pages:
        return pages

    # Página 1 e 2 sempre entram (capa + índice/introdução)
    must_include = pages[:min(2, len(pages))]
    rest = pages[2:]

    remaining_slots = max_pages - len(must_include)
    if remaining_slots <= 0:
        return must_include

    if not rest:
        return must_include

    # Distribui ao longo do documento
    step = max(1, len(rest) // remaining_slots)
    sampled = rest[::step][:remaining_slots]

    # Combina e ordena por número de página
    combined = must_include + sampled
    combined.sort(key=lambda p: p["page_num"])

    return combined[:max_pages]


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_pdf(
    input_path: Path,
    max_pages: int = 10,
) -> Tuple[Path, Path]:
    """
    Anonimiza um PDF.

    Args:
        input_path: Caminho para o PDF em data/real/
        max_pages: Número máximo de páginas a incluir na amostra (padrão: 10)

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimização de PDF: {input_path.name}")

    # --- Extração ---
    all_pages = _extract_pages(input_path)
    total_pages = len(all_pages)
    total_words = sum(p["word_count"] for p in all_pages)
    log.info(f"PDF carregado: {total_pages} páginas, ~{total_words} palavras")

    # --- Amostragem ---
    sample_pages = _sample_pages(all_pages, max_pages)
    log.info(
        f"Amostra selecionada: páginas {[p['page_num'] for p in sample_pages]} "
        f"({len(sample_pages)} de {total_pages})"
    )

    # --- Anonimização ---
    engine = TextAnonymizer()
    anonymized_pages = []

    for page in sample_pages:
        if not page["text"]:
            anonymized_pages.append({**page, "text_anon": "[PÁGINA SEM TEXTO EXTRAÍVEL]"})
            continue

        anon_text = engine.anonymize(page["text"])
        anonymized_pages.append({**page, "text_anon": anon_text})

    log.info(f"Entidades substituídas: {len(engine.entity_map)} ocorrências únicas")
    # Log sem PII — mostra apenas tokens
    for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
        log.info(f"  Substituição #{i+1}: -> '{token}'")

    # --- Montar texto de saída ---
    lines = []
    lines.append("=" * 70)
    lines.append("PSA - PDF ANONIMIZADO")
    lines.append(f"Original: {input_path.name}")
    lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append(f"Páginas incluídas: {[p['page_num'] for p in anonymized_pages]} de {total_pages} total")
    lines.append("=" * 70)

    for page in anonymized_pages:
        lines.append(f"\n{'─' * 60}")
        lines.append(f"PÁGINA {page['page_num']} / {total_pages}")
        if page["has_tables"]:
            lines.append("[contém tabelas]")
        lines.append('─' * 60)
        lines.append(page["text_anon"])

    lines.append(f"\n{'=' * 70}")
    lines.append(f"[FIM DO DOCUMENTO ANONIMIZADO — {len(anonymized_pages)} páginas de {total_pages}]")
    lines.append("=" * 70)

    output_text = "\n".join(lines)

    # --- Salvar arquivo anonimizado ---
    anon_filename = f"anon_{stem}_{timestamp}.txt"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"PDF anonimizado salvo como TXT: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "pdf",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_paginas_original": total_pages,
        "total_palavras_original": total_words,
        "paginas_na_amostra": [p["page_num"] for p in anonymized_pages],
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
        description="PSA Guardião — Anonimizador de PDFs"
    )
    parser.add_argument("arquivo", help="Caminho para o PDF a anonimizar")
    parser.add_argument(
        "--pages",
        type=int,
        default=10,
        metavar="N",
        help="Número máximo de páginas na amostra (padrão: 10)",
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".pdf":
        log.error(f"Arquivo deve ser PDF. Recebido: {input_path.suffix}")
        sys.exit(1)

    anon_path, map_path = anonymize_pdf(input_path, max_pages=args.pages)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
