"""
PSA - Privacy Shield Agent
Script: anonymize_log.py
Responsável: PSA Guardião

Anonimiza arquivos de log (.log):
  - Lê o arquivo linha a linha (com fallback de encoding)
  - Aplica text_engine para detectar CPF, CNPJ, nomes, emails, telefones, etc.
  - Detecta e substitui adicionalmente:
    - Endereços IPv4 → IPs falsos na faixa 10.0.x.x (consistentes)
    - Tokens de sessão (sess_XXXX, tok_XXXX) → [SESSION_N], [TOKEN_N]
    - User-Agent strings → [USER_AGENT_REDACTED]
  - Amostragem inteligente para arquivos com >1000 linhas
  - Salva como .log em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_log.py <caminho_do_arquivo> [--sample <n_linhas>]

Exemplos:
  python3 scripts/anonymize_log.py data/real/servidor.log
  python3 scripts/anonymize_log.py data/real/acesso.log --sample 500
"""

import sys
import re
import json
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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
# Regex para padrões específicos de log
# ---------------------------------------------------------------------------

_IPV4 = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')

_SESSION_TOKEN = re.compile(r'\bsess_[A-Za-z0-9]{4,}\b')
_TOKEN = re.compile(r'\btok_[A-Za-z0-9]{4,}\b')

# User-Agent: detecta strings típicas de navegadores e bots
_USER_AGENT = re.compile(
    r'(?:Mozilla|Opera|Safari|Chrome|Firefox|Edge|MSIE|Trident|Gecko|AppleWebKit|OPR)'
    r'[^\n"]*'
)


# ---------------------------------------------------------------------------
# Anonimização de IPs
# ---------------------------------------------------------------------------

class _IpAnonymizer:
    """Mantém mapeamento consistente de IPs reais → IPs falsos (10.0.x.x)."""

    def __init__(self):
        self._map = {}  # type: Dict[str, str]
        self._counter = 0

    def anonymize(self, ip: str) -> str:
        """Retorna IP falso na faixa 10.0.x.x, consistente para o mesmo IP."""
        if ip in self._map:
            return self._map[ip]

        self._counter += 1
        octet3 = (self._counter // 256) % 256
        octet4 = self._counter % 256
        if octet4 == 0:
            octet4 = 1
        fake_ip = f"10.0.{octet3}.{octet4}"

        self._map[ip] = fake_ip
        return fake_ip

    @property
    def entity_map(self) -> Dict[str, str]:
        return dict(self._map)


# ---------------------------------------------------------------------------
# Anonimização de sessões e tokens
# ---------------------------------------------------------------------------

class _TokenAnonymizer:
    """Mantém mapeamento consistente de tokens de sessão."""

    def __init__(self):
        self._sessions = {}  # type: Dict[str, str]
        self._tokens = {}  # type: Dict[str, str]
        self._session_counter = 0
        self._token_counter = 0

    def anonymize_session(self, value: str) -> str:
        if value in self._sessions:
            return self._sessions[value]
        self._session_counter += 1
        placeholder = f"[SESSION_{self._session_counter}]"
        self._sessions[value] = placeholder
        return placeholder

    def anonymize_token(self, value: str) -> str:
        if value in self._tokens:
            return self._tokens[value]
        self._token_counter += 1
        placeholder = f"[TOKEN_{self._token_counter}]"
        self._tokens[value] = placeholder
        return placeholder

    @property
    def entity_map(self) -> Dict[str, str]:
        result = {}
        result.update(self._sessions)
        result.update(self._tokens)
        return result


# ---------------------------------------------------------------------------
# Leitura do arquivo com fallback de encoding
# ---------------------------------------------------------------------------

def _read_lines(path: Path) -> List[str]:
    """Lê todas as linhas do arquivo .log com fallback de encoding."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                lines = f.readlines()
            log.info(f"Encoding detectado: {enc}")
            return lines
        except UnicodeDecodeError:
            continue

    # Último recurso: utf-8 com replace
    log.warning(f"Encoding não detectado para '{path.name}', usando UTF-8 com replace")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


# ---------------------------------------------------------------------------
# Amostragem inteligente
# ---------------------------------------------------------------------------

def _calculate_sample_size(n: int) -> int:
    """Calcula tamanho de amostra (mesma lógica de anonymizer.py)."""
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


def _sample_lines(
    lines: List[str],
    sample_size: Optional[int],
) -> List[str]:
    """
    Seleciona amostra de linhas se o arquivo tiver >1000 linhas.
    Mantém distribuição proporcional: início, meio e fim.
    """
    total = len(lines)

    if total <= 1000 and sample_size is None:
        return lines

    if sample_size is None:
        sample_size = _calculate_sample_size(total)

    if sample_size >= total:
        return lines

    # Distribuição: 40% início, 40% meio, 20% fim
    n_start = int(sample_size * 0.4)
    n_mid = int(sample_size * 0.4)
    n_end = sample_size - n_start - n_mid

    mid_offset = (total // 2) - (n_mid // 2)

    selected_indices = set()
    selected_indices.update(range(0, n_start))
    selected_indices.update(range(mid_offset, mid_offset + n_mid))
    selected_indices.update(range(total - n_end, total))

    result = [lines[i] for i in sorted(selected_indices)]

    log.info(
        f"Amostra selecionada: {len(result)} de {total} linhas "
        f"({len(result) * 100 / total:.1f}%)"
    )

    return result


# ---------------------------------------------------------------------------
# Anonimização de uma linha de log
# ---------------------------------------------------------------------------

def _anonymize_line(
    line: str,
    engine: TextAnonymizer,
    ip_anon: _IpAnonymizer,
    token_anon: _TokenAnonymizer,
) -> str:
    """Aplica todas as camadas de anonimização a uma linha de log."""
    result = line

    # 1) User-Agent (antes do text_engine para evitar conflito com nomes)
    result = _USER_AGENT.sub("[USER_AGENT_REDACTED]", result)

    # 2) text_engine: CPF, CNPJ, nomes, emails, telefones, etc.
    result = engine.anonymize(result)

    # 3) IPs (text_engine não cobre IPv4)
    def _replace_ip(match):
        return ip_anon.anonymize(match.group(0))
    result = _IPV4.sub(_replace_ip, result)

    # 4) Tokens de sessão
    def _replace_session(match):
        return token_anon.anonymize_session(match.group(0))
    result = _SESSION_TOKEN.sub(_replace_session, result)

    # 5) Tokens genéricos
    def _replace_token(match):
        return token_anon.anonymize_token(match.group(0))
    result = _TOKEN.sub(_replace_token, result)

    return result


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_log(
    input_path: Path,
    sample_size: Optional[int] = None,
) -> Tuple[Path, Path]:
    """
    Anonimiza um arquivo de log (.log).

    Args:
        input_path: Caminho para o arquivo .log
        sample_size: Número de linhas na amostra (None = automático,
                     amostragem ativada apenas para >1000 linhas)

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimização de log: {input_path.name}")

    # --- Leitura ---
    lines = _read_lines(input_path)
    total_lines = len(lines)
    log.info(f"Log carregado: {total_lines} linhas")

    # --- Amostragem ---
    sampled = _sample_lines(lines, sample_size)
    sampled_count = len(sampled)

    if sampled_count < total_lines:
        log.info(
            f"Amostragem aplicada: {sampled_count} de {total_lines} linhas "
            f"({sampled_count * 100 / total_lines:.1f}%)"
        )
    else:
        log.info(f"Processando todas as {total_lines} linhas (sem amostragem)")

    # --- Anonimização ---
    engine = TextAnonymizer()
    ip_anon = _IpAnonymizer()
    token_anon = _TokenAnonymizer()

    anonymized_lines = []
    for line in sampled:
        anon_line = _anonymize_line(line, engine, ip_anon, token_anon)
        anonymized_lines.append(anon_line)

    log.info(f"Entidades substituídas: {len(engine.entity_map)} ocorrências únicas (text_engine)")
    log.info(f"IPs substituídos: {len(ip_anon.entity_map)} endereços únicos")
    log.info(f"Tokens substituídos: {len(token_anon.entity_map)} tokens únicos")

    for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
        log.info(f"  Substituição #{i+1}: -> '{token}'")

    # --- Montar saída ---
    output_lines = []
    output_lines.append("=" * 70)
    output_lines.append("PSA - LOG ANONIMIZADO")
    output_lines.append(f"Original: {input_path.name}")
    output_lines.append(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    output_lines.append(f"Linhas: {sampled_count} de {total_lines}")
    if sampled_count < total_lines:
        output_lines.append(f"Amostragem: {sampled_count * 100 / total_lines:.1f}%")
    output_lines.append("=" * 70)
    output_lines.append("")

    for line in anonymized_lines:
        # Preserva quebra de linha original se existir
        output_lines.append(line.rstrip("\n\r"))

    output_lines.append("")
    output_lines.append("=" * 70)

    output_text = "\n".join(output_lines)

    # --- Salvar arquivo anonimizado ---
    anon_filename = f"anon_{stem}_{timestamp}.log"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"Log anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "log",
        "formato_original": ".log",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_linhas_original": total_lines,
        "total_linhas_amostra": sampled_count,
        "entidades": {
            token: original
            for token, original in engine.entity_map.items()
        },
        "ips_mapeados": ip_anon.entity_map,
        "tokens_mapeados": token_anon.entity_map,
        "estatisticas": {
            "pessoas_substituidas": engine._counters["pessoa"],
            "empresas_substituidas": engine._counters["empresa"],
            "total_entidades": len(engine.entity_map),
            "total_ips": len(ip_anon.entity_map),
            "total_tokens": len(token_anon.entity_map),
        },
    }

    map_filename = f"map_{stem}_{timestamp}.json"
    map_path = MAPS_DIR / map_filename
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa salvo: {map_path}")
    log.info(
        f"Anonimização concluída: {engine._counters['pessoa']} pessoas, "
        f"{engine._counters['empresa']} empresas, "
        f"{len(ip_anon.entity_map)} IPs, "
        f"{len(token_anon.entity_map)} tokens substituídos."
    )

    return anon_path, map_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Anonimizador de arquivos de log"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo .log a anonimizar")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Número de linhas na amostra (padrão: automático para >1000 linhas)",
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".log":
        log.error(f"Formato não suportado: {input_path.suffix}. Use .log")
        sys.exit(1)

    anon_path, map_path = anonymize_log(input_path, sample_size=args.sample)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
