"""
PSA - Privacy Shield Agent
Script: psa.py
Interface unificada do PSA Guardião

Detecta automaticamente o tipo de arquivo e chama o anonimizador correto.
Ponto de entrada principal para toda operação de anonimização.

Formatos suportados:
  Planilhas    : .csv, .xlsx, .xls
  Documentos   : .docx, .txt
  PDFs         : .pdf
  Apresentações: .pptx
  Emails       : .eml, .msg

Uso:
  python3 scripts/psa.py <arquivo>                     # anonimiza com padrões
  python3 scripts/psa.py <arquivo> --sample 50         # planilha: 50 linhas
  python3 scripts/psa.py <arquivo> --pages 5           # PDF: 5 páginas
  python3 scripts/psa.py <arquivo> --paragraphs 30     # documento: 30 parágrafos
  python3 scripts/psa.py <arquivo> --slides 20         # apresentação: 20 slides
  python3 scripts/psa.py data/real/                    # processa pasta inteira
  python3 scripts/psa.py --list-supported              # lista formatos suportados

Exemplos:
  python3 scripts/psa.py data/real/clientes.xlsx
  python3 scripts/psa.py data/real/contrato.docx --paragraphs 15
  python3 scripts/psa.py data/real/relatorio.pdf --pages 4
  python3 scripts/psa.py data/real/pitch.pptx
  python3 scripts/psa.py data/real/proposta.eml
  python3 scripts/psa.py data/real/                    # tudo na pasta
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BASE_DIR / "scripts"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento de extensões → scripts
# ---------------------------------------------------------------------------

SUPPORTED = {
    # Planilhas
    ".csv":  ("spreadsheet", "CSV"),
    ".xlsx": ("spreadsheet", "Excel"),
    ".xls":  ("spreadsheet", "Excel legado"),
    # Documentos
    ".docx": ("document",    "Word"),
    ".txt":  ("document",    "Texto"),
    # PDF
    ".pdf":  ("pdf",         "PDF"),
    # Apresentações
    ".pptx": ("presentation", "PowerPoint"),
    # Emails
    ".eml":  ("email",       "Email EML"),
    ".msg":  ("email",       "Email MSG (Outlook)"),
}

# H-08: Diretórios protegidos — inclui logs/
PROTECTED_DIRS = {"real", "samples", "maps", "logs"}


def _check_protected(path: Path) -> bool:
    """
    H-08: Verifica se o caminho de SAÍDA está em diretório protegido.
    Retorna True se protegido (deve bloquear escrita).
    """
    parts = {p.name for p in path.resolve().parents}
    return bool(parts & PROTECTED_DIRS)


# ---------------------------------------------------------------------------
# Validação de segurança pré-execução
# ---------------------------------------------------------------------------

def _security_check(path: Path) -> bool:
    """
    H-09/H-10: Verifica se o arquivo está em local seguro para processar.
    Bloqueia:
      - data/anonymized/ (não re-anonimizar)
      - data/maps/ (protegido)
      - data/samples/ (protegido)
      - logs/ (protegido)
    """
    resolved = path.resolve()

    blocked_dirs = [
        (BASE_DIR / "data" / "anonymized").resolve(),
        (BASE_DIR / "data" / "maps").resolve(),
        (BASE_DIR / "data" / "samples").resolve(),
        (BASE_DIR / "logs").resolve(),
    ]

    for blocked in blocked_dirs:
        if str(resolved).startswith(str(blocked)):
            dir_name = blocked.name
            log.error(
                f"BLOQUEADO: '{path.name}' está em diretório protegido ({dir_name}/).\n"
                f"O PSA só processa arquivos em data/real/ ou caminhos externos."
            )
            return False

    return True


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _anonymize(
    input_path: Path,
    sample: int = 100,
    pages: int = 10,
    paragraphs: int = 20,
    slides: int = 15,
) -> Optional[Tuple[Path, Path]]:
    """
    Detecta o tipo do arquivo e despacha para o anonimizador correto.
    Retorna (anon_path, map_path) ou None em caso de erro.
    """
    suffix = input_path.suffix.lower()

    if suffix not in SUPPORTED:
        log.error(
            f"Formato não suportado: '{suffix}'\n"
            f"Formatos aceitos: {', '.join(sorted(SUPPORTED.keys()))}"
        )
        return None

    kind, label = SUPPORTED[suffix]
    log.info(f"Arquivo detectado como: {label} ({suffix})")

    try:
        if kind == "spreadsheet":
            from anonymizer import anonymize_spreadsheet
            return anonymize_spreadsheet(input_path, sample_size=sample)

        elif kind == "document":
            from anonymize_document import anonymize_document
            return anonymize_document(input_path, sample_paragraphs=paragraphs)

        elif kind == "pdf":
            from anonymize_pdf import anonymize_pdf
            return anonymize_pdf(input_path, max_pages=pages)

        elif kind == "presentation":
            from anonymize_presentation import anonymize_presentation
            return anonymize_presentation(input_path, max_slides=slides)

        elif kind == "email":
            from anonymize_email import anonymize_email
            return anonymize_email(input_path)

    except ImportError as e:
        log.error(f"Dependência ausente: {e}")
        return None
    except Exception as e:
        log.error(f"Erro ao anonimizar '{input_path.name}': {e}")
        import traceback
        traceback.print_exc()
        return None


def _process_folder(
    folder: Path,
    sample: int,
    pages: int,
    paragraphs: int,
    slides: int,
) -> List[dict]:
    """Processa todos os arquivos suportados em uma pasta (não recursivo)."""
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED
    ]

    if not files:
        log.warning(f"Nenhum arquivo suportado encontrado em: {folder}")
        return []

    log.info(f"Processando {len(files)} arquivo(s) em: {folder}")

    results = []
    for f in sorted(files):
        log.info(f"\n{'─' * 50}")
        # H-10: Aplica security_check a cada arquivo na pasta
        if not _security_check(f):
            results.append({"arquivo": f.name, "status": "erro"})
            continue
        result = _anonymize(f, sample=sample, pages=pages, paragraphs=paragraphs, slides=slides)
        if result:
            anon_path, map_path = result
            results.append({
                "arquivo": f.name,
                "status": "ok",
                "anonimizado": str(anon_path),
                "mapa": str(map_path),
            })
        else:
            results.append({"arquivo": f.name, "status": "erro"})

    return results


# ---------------------------------------------------------------------------
# Relatório de operação
# ---------------------------------------------------------------------------

def _save_operation_log(results: List[dict], input_path: Path):
    """Salva log estruturado da operação em logs/."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "entrada": str(input_path),
        "total": len(results),
        "sucesso": sum(1 for r in results if r.get("status") == "ok"),
        "erro": sum(1 for r in results if r.get("status") == "erro"),
        "arquivos": results,
    }
    log_path = LOGS_DIR / f"operacao_{timestamp}.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    return log_path


def _print_summary(results: List[dict]):
    """Exibe tabela resumo no terminal."""
    print("\n" + "=" * 70)
    print("PSA GUARDIÃO — RESUMO DA OPERAÇÃO")
    print("=" * 70)
    ok = [r for r in results if r.get("status") == "ok"]
    err = [r for r in results if r.get("status") == "erro"]

    for r in ok:
        print(f"  ✓ {r['arquivo']}")
        print(f"    → {r['anonimizado']}")

    for r in err:
        print(f"  ✗ {r['arquivo']} — ERRO")

    print("─" * 70)
    print(f"  Total: {len(results)} arquivo(s) | {len(ok)} ok | {len(err)} erro(s)")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Interface unificada de anonimização",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formatos suportados:
  Planilhas    : .csv, .xlsx, .xls
  Documentos   : .docx, .txt
  PDFs         : .pdf
  Apresentações: .pptx
  Emails       : .eml, .msg

Exemplos:
  python3 scripts/psa.py data/real/clientes.xlsx
  python3 scripts/psa.py data/real/contrato.docx --paragraphs 15
  python3 scripts/psa.py data/real/relatorio.pdf --pages 4
  python3 scripts/psa.py data/real/pitch.pptx --slides 10
  python3 scripts/psa.py data/real/proposta.eml
  python3 scripts/psa.py data/real/        (processa pasta inteira)
        """,
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        help="Arquivo ou pasta a anonimizar (pasta: processa todos os arquivos suportados)",
    )
    parser.add_argument(
        "--sample", type=int, default=100, metavar="N",
        help="[Planilhas] Máximo de linhas na amostra (padrão: 100)",
    )
    parser.add_argument(
        "--pages", type=int, default=10, metavar="N",
        help="[PDF] Máximo de páginas na amostra (padrão: 10)",
    )
    parser.add_argument(
        "--paragraphs", type=int, default=20, metavar="N",
        help="[Documentos] Máximo de parágrafos na amostra (padrão: 20)",
    )
    parser.add_argument(
        "--slides", type=int, default=15, metavar="N",
        help="[Apresentações] Máximo de slides na amostra (padrão: 15)",
    )
    parser.add_argument(
        "--list-supported", action="store_true",
        help="Lista os formatos suportados e sai",
    )

    args = parser.parse_args()

    if args.list_supported:
        print("\nFormatos suportados pelo PSA:\n")
        for ext, (kind, label) in sorted(SUPPORTED.items()):
            print(f"  {ext:8}  {label}")
        print()
        sys.exit(0)

    if not args.entrada:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.entrada)

    if not input_path.exists():
        log.error(f"Caminho não encontrado: {input_path}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("PSA — PRIVACY SHIELD AGENT")
    print("Guardião ativo. Nenhum dado real sairá sem anonimização.")
    print("=" * 70)

    # --- Pasta: processa múltiplos arquivos ---
    if input_path.is_dir():
        # H-10: Security check na pasta inteira
        if not _security_check(input_path / "_dummy"):
            sys.exit(1)
        results = _process_folder(
            input_path,
            sample=args.sample,
            pages=args.pages,
            paragraphs=args.paragraphs,
            slides=args.slides,
        )
        if results:
            log_path = _save_operation_log(results, input_path)
            _print_summary(results)
            print(f"\n  Log da operação: {log_path}")
        n_err = sum(1 for r in results if r.get("status") == "erro")
        sys.exit(1 if n_err else 0)

    # --- Arquivo único ---
    if not _security_check(input_path):
        sys.exit(1)

    result = _anonymize(
        input_path,
        sample=args.sample,
        pages=args.pages,
        paragraphs=args.paragraphs,
        slides=args.slides,
    )

    if result:
        anon_path, map_path = result
        _print_summary([{
            "arquivo": input_path.name,
            "status": "ok",
            "anonimizado": str(anon_path),
            "mapa": str(map_path),
        }])
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
