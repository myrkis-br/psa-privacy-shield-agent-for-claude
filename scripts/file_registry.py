"""
PSA - Privacy Shield Agent
Módulo: file_registry.py

Registro local de nomes de arquivos.
Substitui nomes reais por códigos genéricos (DOC_001, DOC_002, etc.)
para que nenhum nome de arquivo real saia do computador.

O registro é salvo em data/maps/file_registry.json (local, protegido).

Uso via psa.py:
  python3 scripts/psa.py --register data/real/clientes.xlsx
  python3 scripts/psa.py --register data/real/           # pasta inteira
  python3 scripts/psa.py --list-files                    # lista arquivos registrados
  python3 scripts/psa.py DOC_001                         # anonimiza pelo código
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MAPS_DIR = BASE_DIR / "data" / "maps"
REGISTRY_PATH = MAPS_DIR / "file_registry.json"

MAPS_DIR.mkdir(parents=True, exist_ok=True)


def _load_registry() -> Dict:
    """Carrega o registro do disco."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"next_id": 1, "files": {}}


def _save_registry(registry: Dict) -> None:
    """Salva o registro no disco."""
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def register_file(real_path: Path) -> Tuple[str, str]:
    """
    Registra um arquivo e retorna (código_genérico, extensão).

    Se o arquivo já estiver registrado (mesmo caminho absoluto),
    retorna o código existente sem duplicar.

    Returns:
        Tuple (code, suffix) ex: ("DOC_001", ".xlsx")
    """
    real_path = Path(real_path).resolve()
    if not real_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {real_path}")
    if not real_path.is_file():
        raise ValueError(f"Não é um arquivo: {real_path}")

    registry = _load_registry()
    real_str = str(real_path)

    # Verifica se já está registrado
    for code, entry in registry["files"].items():
        if entry["real_path"] == real_str:
            log.info(f"Arquivo já registrado: {code}{entry['suffix']}")
            return code, entry["suffix"]

    # Novo registro
    file_id = registry["next_id"]
    code = f"DOC_{file_id:03d}"
    suffix = real_path.suffix.lower()

    registry["files"][code] = {
        "real_path": real_str,
        "real_name": real_path.name,
        "suffix": suffix,
        "registered_at": datetime.now().isoformat(),
    }
    registry["next_id"] = file_id + 1

    _save_registry(registry)
    log.info(f"Registrado: {code}{suffix} (arquivo real protegido)")
    return code, suffix


def register_folder(folder_path: Path, supported_exts: set) -> List[Tuple[str, str, str]]:
    """
    Registra todos os arquivos suportados em uma pasta.

    Args:
        folder_path: Caminho da pasta
        supported_exts: Set de extensões suportadas (ex: {".csv", ".xlsx"})

    Returns:
        Lista de (code, suffix, real_name) para cada arquivo registrado
    """
    folder_path = Path(folder_path).resolve()
    if not folder_path.is_dir():
        raise ValueError(f"Não é um diretório: {folder_path}")

    results = []
    for f in sorted(folder_path.iterdir()):
        if f.is_file() and f.suffix.lower() in supported_exts:
            code, suffix = register_file(f)
            results.append((code, suffix, f.name))

    return results


def resolve_code(code: str) -> Optional[Path]:
    """
    Resolve um código genérico para o caminho real.

    Args:
        code: Código como "DOC_001" ou "DOC_001.xlsx"

    Returns:
        Path real ou None se não encontrado
    """
    # Remove extensão se fornecida (ex: "DOC_001.xlsx" -> "DOC_001")
    clean = code.upper().split(".")[0] if "." in code else code.upper()

    registry = _load_registry()
    entry = registry["files"].get(clean)
    if entry is None:
        return None

    real_path = Path(entry["real_path"])
    if not real_path.exists():
        log.warning(f"Arquivo registrado mas não encontrado no disco: {clean}")
        return None

    return real_path


def is_doc_code(value: str) -> bool:
    """Verifica se o valor parece ser um código DOC_NNN."""
    import re
    clean = value.strip().upper().split(".")[0] if "." in value else value.strip().upper()
    return bool(re.match(r'^DOC_\d{3,}$', clean))


def list_registered() -> List[Dict]:
    """
    Lista todos os arquivos registrados.

    Returns:
        Lista de dicts com code, suffix, registered_at (SEM real_name/real_path)
    """
    registry = _load_registry()
    result = []
    for code, entry in registry["files"].items():
        result.append({
            "code": code,
            "suffix": entry["suffix"],
            "registered_at": entry["registered_at"],
        })
    return result


def get_code_for_path(real_path: Path) -> Optional[str]:
    """Retorna o código genérico de um arquivo já registrado, ou None."""
    real_str = str(Path(real_path).resolve())
    registry = _load_registry()
    for code, entry in registry["files"].items():
        if entry["real_path"] == real_str:
            return code
    return None


def get_history(code: str) -> Optional[Dict]:
    """
    Retorna o histórico de anonimizações de um código DOC_NNN.

    Busca em data/anonymized/ e data/maps/ por arquivos cujo nome base
    corresponda ao arquivo real registrado sob esse código.

    Returns:
        Dict com info do registro + lista de execuções, ou None se código inválido.
    """
    clean = code.upper().split(".")[0] if "." in code else code.upper()
    registry = _load_registry()
    entry = registry["files"].get(clean)
    if entry is None:
        return None

    real_name = entry["real_name"]
    stem = Path(real_name).stem  # ex: "peticao_mpf_agua"

    ANONYMIZED_DIR = BASE_DIR / "data" / "anonymized"
    MAPS_DIR_LOCAL = BASE_DIR / "data" / "maps"

    # Busca arquivos anonimizados que contenham o stem no nome
    anon_files = sorted(
        [f for f in ANONYMIZED_DIR.iterdir() if f.is_file() and stem in f.name],
        key=lambda f: f.stat().st_mtime,
    ) if ANONYMIZED_DIR.exists() else []

    executions = []  # type: List[Dict]
    for anon_file in anon_files:
        # Tenta encontrar o mapa correspondente pelo timestamp
        # anon_peticao_mpf_agua_20260311_094500.txt → map_peticao_mpf_agua_20260311_094500.json
        anon_name = anon_file.stem  # sem extensão
        # Extrai timestamp: últimos 15 chars antes da extensão (YYYYMMDD_HHMMSS)
        parts = anon_name.split("_")
        timestamp_str = None
        for i in range(len(parts) - 1):
            candidate = parts[i] + "_" + parts[i + 1]
            if len(candidate) == 15 and candidate.replace("_", "").isdigit():
                timestamp_str = candidate
                break

        # Busca mapa correspondente
        map_file = None
        entities = None
        if timestamp_str:
            map_candidates = [
                f for f in MAPS_DIR_LOCAL.iterdir()
                if f.is_file() and stem in f.name and timestamp_str in f.name and f.suffix == ".json"
            ] if MAPS_DIR_LOCAL.exists() else []
            if map_candidates:
                map_file = map_candidates[0]
                try:
                    with open(map_file, "r", encoding="utf-8") as mf:
                        map_data = json.load(mf)
                    tipo = map_data.get("tipo", "spreadsheet")
                    if tipo == "pdf":
                        stats = map_data.get("estatisticas", {})
                        pages_sample = map_data.get("paginas_na_amostra", [])
                        entities = {
                            "tipo": "pdf",
                            "total_paginas": map_data.get("total_paginas_original"),
                            "paginas_amostra": len(pages_sample),
                            "total_palavras": map_data.get("total_palavras_original"),
                            "pessoas_substituidas": stats.get("pessoas_substituidas", 0),
                            "empresas_substituidas": stats.get("empresas_substituidas", 0),
                            "total_entidades": stats.get("total_entidades", 0),
                        }
                    elif tipo == "document":
                        stats = map_data.get("estatisticas", {})
                        entities = {
                            "tipo": "document",
                            "total_paragrafos": map_data.get("total_paragrafos_original"),
                            "paragrafos_amostra": map_data.get("paragrafos_na_amostra"),
                            "pessoas_substituidas": stats.get("pessoas_substituidas", 0),
                            "empresas_substituidas": stats.get("empresas_substituidas", 0),
                            "total_entidades": stats.get("total_entidades", 0),
                        }
                    else:
                        # Planilha (CSV/XLSX)
                        entities = {
                            "tipo": "spreadsheet",
                            "total_linhas_original": map_data.get("total_linhas_original"),
                            "total_linhas_amostra": map_data.get("total_linhas_amostra"),
                            "pct_enviado": map_data.get("pct_enviado"),
                            "pct_economizado": map_data.get("pct_economizado"),
                            "amostragem": map_data.get("amostragem"),
                        }
                        cols = map_data.get("colunas", {})
                        entities["colunas_anonimizadas"] = sum(1 for c in cols.values() if c.get("anonimizada"))
                        entities["colunas_texto_livre"] = sum(1 for c in cols.values() if c.get("texto_livre"))
                except (json.JSONDecodeError, KeyError):
                    pass

        # Formato de data legível a partir do mtime
        mtime = anon_file.stat().st_mtime
        dt = datetime.fromtimestamp(mtime)

        executions.append({
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "anon_file": str(anon_file),
            "anon_size": anon_file.stat().st_size,
            "map_file": str(map_file) if map_file else None,
            "entities": entities,
        })

    return {
        "code": clean,
        "suffix": entry["suffix"],
        "registered_at": entry["registered_at"],
        "total_executions": len(executions),
        "executions": executions,
    }
