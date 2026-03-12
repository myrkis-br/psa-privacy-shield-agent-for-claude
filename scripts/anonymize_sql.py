"""
PSA - Privacy Shield Agent
Script: anonymize_sql.py
Responsável: PSA Guardião

Anonimiza arquivos SQL (dumps, scripts DDL/DML):
  - Preserva toda a estrutura SQL: CREATE TABLE, DROP, ALTER, INDEX, GRANT
  - Anonimiza apenas string literals ('...') dentro de INSERT/VALUES
  - Anonimiza comentários SQL que contenham PII (-- linhas de comentário)
  - Preserva palavras-chave SQL, nomes de tabela, nomes de coluna
  - Aplica text_engine para detectar CPF, CNPJ, nomes, emails, etc.
  - Salva como .sql anonimizado em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_sql.py <caminho_do_arquivo> [--sample <n_linhas>]

Exemplos:
  python3 scripts/anonymize_sql.py data/real/dump.sql
  python3 scripts/anonymize_sql.py data/real/dump.sql --sample 500
"""

import re
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

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
# Regex para string literals SQL
# ---------------------------------------------------------------------------

_STRING_LITERAL_RE = re.compile(r"'([^']*?)'")

# Palavras-chave que indicam linhas com dados (case-insensitive)
_INSERT_KEYWORDS = re.compile(
    r"\b(INSERT\s+INTO|VALUES)\b", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Amostragem inteligente
# ---------------------------------------------------------------------------

def _calculate_sample_size(n: int) -> int:
    """Calcula tamanho de amostra para linhas SQL (mesma lógica de planilhas)."""
    if n <= 30:
        return n
    elif n <= 100:
        return max(30, n // 2)
    elif n <= 10000:
        return 100
    elif n <= 100000:
        return 150
    else:
        return 200


# ---------------------------------------------------------------------------
# Classificação de linhas SQL
# ---------------------------------------------------------------------------

def _is_insert_line(line: str) -> bool:
    """Verifica se a linha contém INSERT INTO ou VALUES keywords."""
    return bool(_INSERT_KEYWORDS.search(line))


def _is_data_row(line: str) -> bool:
    """Verifica se a linha é uma linha de dados dentro de um bloco VALUES.
    Ex:  ('Ana Carolina', '123.456.789-00', ...),
    """
    stripped = line.lstrip()
    return stripped.startswith("(") and "'" in stripped


def _is_comment_line(line: str) -> bool:
    """Verifica se a linha é um comentário SQL de linha única."""
    stripped = line.lstrip()
    return stripped.startswith("--")


def _is_block_comment_line(line: str) -> bool:
    """Verifica se a linha contém comentário de bloco /* ... */."""
    stripped = line.lstrip()
    return stripped.startswith("/*") or stripped.startswith("*")


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_sql(
    input_path: Path,
    sample_size: Optional[int] = None,
) -> Tuple[Path, Path]:
    """
    Anonimiza um arquivo SQL.

    Args:
        input_path: Caminho para o arquivo .sql
        sample_size: Número máximo de linhas na amostra (None = automático)

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimização SQL: {input_path.name}")

    # --- Leitura com fallback de encoding ---
    content = None
    used_encoding = None

    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            content = input_path.read_text(encoding=enc)
            used_encoding = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        content = input_path.read_text(encoding="utf-8", errors="replace")
        used_encoding = "utf-8 (replace)"
        log.warning(
            f"Encoding não detectado para '{input_path.name}', "
            "usando UTF-8 com replace"
        )

    log.info(f"Encoding detectado: {used_encoding}")

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    log.info(f"SQL carregado: {total_lines} linhas")

    # --- Amostragem ---
    if sample_size is None:
        effective_sample = _calculate_sample_size(total_lines)
    else:
        effective_sample = min(sample_size, total_lines)

    # Para SQL, processamos TODAS as linhas (para manter estrutura íntegra),
    # mas só aplicamos anonimização nas primeiras `effective_sample` linhas
    # que contenham dados (INSERT/VALUES ou comentários com PII).
    # Linhas estruturais (DDL) passam sempre intactas.
    log.info(
        f"Amostra: até {effective_sample} linhas de dados serão anonimizadas "
        f"de {total_lines} linhas totais"
    )

    # --- Anonimização ---
    engine = TextAnonymizer()
    anonymized_lines = []
    data_lines_processed = 0
    insert_lines_found = 0
    comment_lines_found = 0
    literals_anonymized = 0
    in_values_block = False  # rastreia blocos multi-linha INSERT...VALUES

    def _replace_literal(match):
        nonlocal literals_anonymized
        original_content = match.group(1)
        if not original_content.strip():
            return match.group(0)  # preserva strings vazias ''
        anon_content = engine.anonymize(original_content)
        literals_anonymized += 1
        return f"'{anon_content}'"

    for line in lines:
        # Linha de comentário SQL (-- ...)
        if _is_comment_line(line):
            in_values_block = False
            comment_lines_found += 1

            if data_lines_processed < effective_sample:
                stripped = line.lstrip()
                prefix_len = len(line) - len(stripped)
                prefix = line[:prefix_len]

                # Extrai texto após '--'
                comment_marker = stripped[:2]  # '--'
                comment_text = stripped[2:]

                if comment_text.strip():
                    anon_comment = engine.anonymize(comment_text)
                    anonymized_lines.append(
                        f"{prefix}{comment_marker}{anon_comment}"
                    )
                    data_lines_processed += 1
                else:
                    anonymized_lines.append(line)
            else:
                anonymized_lines.append(line)
            continue

        # Linha com INSERT/VALUES — anonimiza string literals e ativa bloco
        if _is_insert_line(line):
            in_values_block = True
            insert_lines_found += 1

            if data_lines_processed < effective_sample:
                anon_line = _STRING_LITERAL_RE.sub(_replace_literal, line)
                anonymized_lines.append(anon_line)
                data_lines_processed += 1
            else:
                anonymized_lines.append(line)

            # Se a linha termina com ';' o bloco acabou
            if line.rstrip().endswith(";"):
                in_values_block = False
            continue

        # Linha de dados dentro de bloco VALUES (sem keyword INSERT/VALUES)
        if in_values_block and _is_data_row(line):
            insert_lines_found += 1

            if data_lines_processed < effective_sample:
                anon_line = _STRING_LITERAL_RE.sub(_replace_literal, line)
                anonymized_lines.append(anon_line)
                data_lines_processed += 1
            else:
                anonymized_lines.append(line)

            # Se a linha termina com ';' o bloco acabou
            if line.rstrip().endswith(";"):
                in_values_block = False
            continue

        # Qualquer outra linha (DDL, estrutural) — passa intacta
        in_values_block = False
        anonymized_lines.append(line)

    log.info(
        f"SQL processado: {insert_lines_found} linhas INSERT/VALUES, "
        f"{comment_lines_found} linhas de comentário"
    )
    log.info(f"Literals anonimizados: {literals_anonymized}")
    log.info(f"Entidades substituídas: {len(engine.entity_map)} ocorrências únicas")

    for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
        log.info(f"  Substituição #{i+1}: -> '{token}'")

    # --- Salvar arquivo anonimizado ---
    output_text = "".join(anonymized_lines)
    anon_filename = f"anon_{stem}_{timestamp}.sql"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"SQL anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "database",
        "formato_original": ".sql",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "encoding": used_encoding,
        "total_linhas": total_lines,
        "linhas_insert": insert_lines_found,
        "linhas_comentario": comment_lines_found,
        "literals_anonimizados": literals_anonymized,
        "linhas_dados_processadas": data_lines_processed,
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
        description="PSA Guardião — Anonimizador de arquivos SQL"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo SQL a anonimizar")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Número máximo de linhas de dados a anonimizar (padrão: automático)",
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".sql":
        log.error(f"Formato não suportado: {input_path.suffix}. Use .sql")
        sys.exit(1)

    anon_path, map_path = anonymize_sql(input_path, sample_size=args.sample)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
