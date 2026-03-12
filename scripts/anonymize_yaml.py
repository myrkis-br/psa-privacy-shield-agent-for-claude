"""
PSA - Privacy Shield Agent
Script: anonymize_yaml.py
Responsavel: PSA Guardiao

Anonimiza arquivos YAML — configs, pipelines CI/CD, docker-compose, etc.

Funcionalidades:
  - Travessia recursiva de estruturas YAML (dicts, lists, scalars)
  - Preserva todas as chaves (dict keys NAO sao anonimizadas)
  - Deteccao de campos senssiveis por nome da chave (password, token, secret, etc.)
  - Substituicao de valores sensiveis por placeholders [CHAVE_REDACTED_N]
  - text_engine para valores de texto livre (captura CPF, email, nomes, telefones)
  - Cache de consistencia (mesmo valor real -> mesmo valor fake)
  - Validacao anti-vazamento (C-01)
  - Preserva estrutura YAML original (aninhamento, listas, tipos)

Chaves sensiveis detectadas:
  password, pass, secret, key, token, api_key, auth, credential, dsn, webhook

Uso:
  python3 scripts/anonymize_yaml.py data/real/config.yaml

Exemplos:
  python3 scripts/anonymize_yaml.py data/real/docker-compose.yaml
  python3 scripts/anonymize_yaml.py data/real/pipeline.yml
"""

import sys
import json
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

# ---------------------------------------------------------------------------
# Configuracao de caminhos
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
    format="%(asctime)s [PSA-Guardiao] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

from text_engine import TextAnonymizer

# ---------------------------------------------------------------------------
# Deteccao de chaves sensiveis
# ---------------------------------------------------------------------------

# Fragmentos que indicam segredos/credenciais no nome da chave
_SECRET_KEY_FRAGMENTS = {
    "password", "pass", "secret", "key", "token",
    "api_key", "auth", "credential", "dsn", "webhook",
}

# Regex compilada para match de fragmentos em nomes de chave
_SECRET_KEY_RE = re.compile(
    r"(?:^|[_\-.])"
    r"(?:" + "|".join(re.escape(f) for f in _SECRET_KEY_FRAGMENTS) + r")"
    r"(?:$|[_\-.])",
    re.IGNORECASE,
)


def _is_secret_key(key: str) -> bool:
    """Verifica se o nome da chave indica um segredo/credencial."""
    k = key.lower().replace("-", "_")
    # Match exato
    if k in _SECRET_KEY_FRAGMENTS:
        return True
    # Match por fragmento (ex: db_password, api_key_v2, auth_token)
    if _SECRET_KEY_RE.search(f"_{k}_"):
        return True
    return False


# ---------------------------------------------------------------------------
# Anonimizador YAML
# ---------------------------------------------------------------------------

class _YamlAnonymizer:
    """Motor de anonimizacao para estruturas YAML."""

    def __init__(self):
        self._engine = TextAnonymizer()
        self._redacted_counter = 0
        self._redacted_cache = {}  # type: Dict[str, str]
        self._entities = {}  # type: Dict[str, int]
        self._fields = set()  # type: Set[str]
        self._sensitive_values = set()  # type: Set[str]

    def _next_redacted(self, value: str) -> str:
        """Gera placeholder [CHAVE_REDACTED_N] com cache de consistencia."""
        if value in self._redacted_cache:
            return self._redacted_cache[value]
        self._redacted_counter += 1
        placeholder = f"[CHAVE_REDACTED_{self._redacted_counter}]"
        self._redacted_cache[value] = placeholder
        return placeholder

    def _anonymize_text(self, text: str) -> str:
        """Aplica text_engine em valor de texto livre."""
        try:
            result = self._engine.anonymize(text)
            if result != text:
                self._entities["text_engine"] = (
                    self._entities.get("text_engine", 0) + 1
                )
            return result
        except Exception:
            return text

    def _walk(self, obj: Any, current_key: str = "") -> Any:
        """Percorre e anonimiza estrutura YAML recursivamente."""
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                # Chaves sao preservadas; apenas valores sao anonimizados
                result[k] = self._walk(v, current_key=str(k))
            return result

        elif isinstance(obj, list):
            return [
                self._walk(item, current_key=current_key)
                for item in obj
            ]

        elif isinstance(obj, str) and current_key:
            # Chave secreta -> placeholder REDACTED
            if _is_secret_key(current_key):
                # Coleta valor original para validacao anti-vazamento (apenas segredos)
                if len(obj) >= 6:
                    self._sensitive_values.add(obj)
                self._fields.add(current_key)
                self._entities["secret"] = (
                    self._entities.get("secret", 0) + 1
                )
                return self._next_redacted(obj)

            # Texto livre -> text_engine (CPF, email, nomes, telefones, etc.)
            if len(obj) > 8:
                scanned = self._anonymize_text(obj)
                if scanned != obj:
                    self._fields.add(f"{current_key} (text_engine)")
                return scanned

            return obj

        elif obj is None:
            return None

        else:
            # int, float, bool — preservar
            return obj

    def anonymize(self, data: Any) -> Tuple[Any, Dict]:
        """
        Anonimiza dados YAML.

        Args:
            data: estrutura YAML parsed (dict, list ou scalar)

        Returns:
            (dados_anonimizados, estatisticas)
        """
        anonymized = self._walk(data)

        stats = {
            "total_entidades": sum(self._entities.values()),
            "entidades_por_tipo": dict(self._entities),
            "campos_anonimizados": sorted(self._fields),
        }

        return anonymized, stats

    def get_entity_map(self) -> Dict[str, str]:
        """Retorna mapa combinado de todas as substituicoes."""
        combined = {}
        # Segredos redacted
        for original, placeholder in self._redacted_cache.items():
            combined[placeholder] = original
        # text_engine
        if hasattr(self._engine, "entity_map"):
            combined.update(self._engine.entity_map)
        return combined


# ---------------------------------------------------------------------------
# Validacao anti-vazamento (C-01)
# ---------------------------------------------------------------------------

def _validate_no_leakage(
    sensitive_values: Set[str],
    anonymized_text: str,
    anon_path: Path,
) -> bool:
    """C-01: Verifica se dados reais nao vazaram para o arquivo anonimizado."""
    leaked = []
    for val in sensitive_values:
        if val in anonymized_text:
            leaked.append(val[:30] + "..." if len(val) > 30 else val)

    if leaked:
        log.error(
            f"VAZAMENTO DETECTADO! {len(leaked)} valor(es) real(is) "
            f"encontrado(s) no YAML anonimizado."
        )
        if anon_path.exists():
            anon_path.unlink()
            log.error(f"Arquivo anonimizado DELETADO: {anon_path}")
        return False

    return True


# ---------------------------------------------------------------------------
# Funcao principal
# ---------------------------------------------------------------------------

def anonymize_yaml(input_path: Path) -> Tuple[Path, Path]:
    """
    Anonimiza um arquivo YAML.

    Args:
        input_path: Caminho para o arquivo .yaml / .yml

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimizacao YAML: {input_path.name}")

    # --- Carrega YAML ---
    content = None
    used_encoding = None

    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            raw = input_path.read_text(encoding=enc)
            content = raw
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        log.error(f"Nao foi possivel ler o arquivo: {input_path}")
        raise ValueError(f"Encoding nao detectado para {input_path.name}")

    log.info(f"Encoding: {used_encoding}")

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        log.error(f"Erro ao parsear YAML: {e}")
        raise ValueError(f"Arquivo YAML invalido: {input_path.name}") from e

    if data is None:
        log.warning("YAML vazio ou sem conteudo parseavel")
        data = {}

    # Info sobre a estrutura
    if isinstance(data, dict):
        log.info(f"YAML object: {len(data)} chaves no raiz")
    elif isinstance(data, list):
        log.info(f"YAML array: {len(data)} elementos")

    # --- Anonimizacao ---
    anonymizer = _YamlAnonymizer()
    anonymized, stats = anonymizer.anonymize(data)

    log.info(
        f"YAML: {stats['total_entidades']} entidades em "
        f"{len(stats['campos_anonimizados'])} campos"
    )

    # --- Gera nomes de saida ---
    anon_filename = f"anon_{stem}_{timestamp}.yaml"
    map_filename = f"map_{stem}_{timestamp}.json"
    anon_path = ANONYMIZED_DIR / anon_filename
    map_path = MAPS_DIR / map_filename

    # --- Salva YAML anonimizado ---
    anon_text = yaml.dump(
        anonymized,
        allow_unicode=True,
        default_flow_style=False,
    )
    anon_path.write_text(anon_text, encoding="utf-8")
    log.info(f"YAML anonimizado salvo: {anon_path}")

    # --- Validacao C-01 ---
    # Verifica apenas valores de chaves secretas (redacted) — valores estruturais
    # como nomes de servico, versoes, etc. nao devem ser verificados
    sensitive_for_check = set()
    for original, _placeholder in anonymizer._redacted_cache.items():
        if len(original) >= 6:
            sensitive_for_check.add(original)

    if not _validate_no_leakage(sensitive_for_check, anon_text, anon_path):
        raise RuntimeError(
            "LeakageError: dados reais detectados no YAML anonimizado"
        )

    # --- Salva mapa ---
    entity_map = anonymizer.get_entity_map()

    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "config",
        "formato_original": ".yaml",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "entidades": entity_map,
        "estatisticas": {
            "total_entidades": stats["total_entidades"],
            "entidades_por_tipo": stats["entidades_por_tipo"],
            "campos_anonimizados": stats["campos_anonimizados"],
        },
    }

    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa salvo: {map_path}")
    log.info(
        f"Anonimizacao concluida: {stats['total_entidades']} entidades "
        f"em {len(stats['campos_anonimizados'])} campos."
    )

    return anon_path, map_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardiao — Anonimizador de arquivos YAML"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo YAML a anonimizar")
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo nao encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() not in (".yaml", ".yml"):
        log.error(f"Formato nao suportado: {input_path.suffix}. Use .yaml ou .yml")
        sys.exit(1)

    anon_path, map_path = anonymize_yaml(input_path)

    print("\n" + "=" * 60)
    print("PSA GUARDIAO — ANONIMIZACAO CONCLUIDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondencia: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
