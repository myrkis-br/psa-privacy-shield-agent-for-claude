"""
PSA - Privacy Shield Agent
Script: anonymize_vcf.py
Responsável: PSA Guardião

Anonimiza arquivos vCard (.vcf):
  - Parse manual de vCard 3.0/4.0 (sem dependências externas)
  - Anonimiza FN, N, EMAIL, TEL, ADR, ORG e NOTE
  - Preserva VERSION, BEGIN, END, REV, TITLE e campos estruturais
  - Mantém consistência: mesmo nome original → mesmo nome fake
  - Aplica text_engine em campos NOTE (pode conter CPF, observações)
  - Salva como .vcf válido em data/anonymized/
  - Salva mapa de entidades em data/maps/

Uso:
  python3 scripts/anonymize_vcf.py <caminho_do_arquivo>

Exemplos:
  python3 scripts/anonymize_vcf.py data/real/contatos.vcf
"""

import os
import sys
import json
import random
import re
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
# Faker pt_BR com seed aleatório
# ---------------------------------------------------------------------------

from faker import Faker

_seed = int.from_bytes(os.urandom(4), "big")
Faker.seed(_seed)
random.seed(_seed)
_fake = Faker("pt_BR")

# ---------------------------------------------------------------------------
# Cache de consistência
# ---------------------------------------------------------------------------

_consistency_cache = {}  # type: Dict[str, str]


def _cached(key: str, generator) -> str:
    """Garante que o mesmo valor original sempre gera o mesmo valor fake."""
    normalized = key.strip().lower()
    if normalized not in _consistency_cache:
        _consistency_cache[normalized] = generator()
    return _consistency_cache[normalized]


# ---------------------------------------------------------------------------
# Geradores de valores fake
# ---------------------------------------------------------------------------

def _fake_full_name(original: str) -> str:
    return _cached(f"name:{original}", _fake.name)


def _fake_email(original: str) -> str:
    return _cached(f"email:{original}", _fake.email)


def _fake_phone(original: str) -> str:
    return _cached(f"phone:{original}", _fake.phone_number)


def _fake_company(original: str) -> str:
    return _cached(f"org:{original}", _fake.company)


def _fake_address_components() -> Dict[str, str]:
    """Gera componentes de endereço fake."""
    return {
        "po_box": "",
        "extended": "",
        "street": _fake.street_address(),
        "city": _fake.city(),
        "region": _fake.estado_nome(),
        "postal_code": _fake.postcode(),
        "country": "Brasil",
    }


# ---------------------------------------------------------------------------
# Parser de vCard
# ---------------------------------------------------------------------------

def _unfold_lines(text: str) -> List[str]:
    """
    Desdobra linhas continuadas no vCard (RFC 6350 §3.2).
    Linhas que começam com espaço ou tab são continuação da anterior.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    unfolded = []  # type: List[str]

    for line in lines:
        if line and (line[0] == " " or line[0] == "\t"):
            if unfolded:
                unfolded[-1] += line[1:]
            else:
                unfolded.append(line[1:])
        else:
            unfolded.append(line)

    return unfolded


def _parse_property(line: str) -> Tuple[str, str, str]:
    """
    Divide uma linha vCard em (nome_campo, parâmetros, valor).
    Exemplos:
        "FN:João Silva"            → ("FN", "", "João Silva")
        "TEL;TYPE=CELL:+55119999"  → ("TEL", "TYPE=CELL", "+55119999")
        "N:Silva;João;;;"          → ("N", "", "Silva;João;;;")
    """
    # Encontra o primeiro ':' que não está dentro de parâmetros quoted
    colon_idx = -1
    in_quotes = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == ':' and not in_quotes:
            colon_idx = i
            break

    if colon_idx == -1:
        return (line, "", "")

    key_part = line[:colon_idx]
    value = line[colon_idx + 1:]

    # Separa nome do campo dos parâmetros (separados por ';')
    if ";" in key_part:
        parts = key_part.split(";", 1)
        field_name = parts[0].upper()
        params = parts[1]
    else:
        field_name = key_part.upper()
        params = ""

    return (field_name, params, value)


def _parse_vcards(text: str) -> List[List[Tuple[str, str, str]]]:
    """
    Parseia texto vCard em lista de contatos.
    Cada contato é uma lista de (nome_campo, parâmetros, valor).
    """
    lines = _unfold_lines(text)
    cards = []  # type: List[List[Tuple[str, str, str]]]
    current_card = None  # type: Optional[List[Tuple[str, str, str]]]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        field_name, params, value = _parse_property(stripped)

        if field_name == "BEGIN" and value.upper() == "VCARD":
            current_card = []
            current_card.append((field_name, params, value))
        elif field_name == "END" and value.upper() == "VCARD":
            if current_card is not None:
                current_card.append((field_name, params, value))
                cards.append(current_card)
                current_card = None
        elif current_card is not None:
            current_card.append((field_name, params, value))

    return cards


def _serialize_vcards(cards: List[List[Tuple[str, str, str]]]) -> str:
    """Serializa contatos de volta para formato vCard."""
    output_lines = []  # type: List[str]

    for card in cards:
        for field_name, params, value in card:
            if params:
                line = f"{field_name};{params}:{value}"
            else:
                line = f"{field_name}:{value}"
            output_lines.append(line)
        output_lines.append("")  # linha em branco entre contatos

    return "\r\n".join(output_lines)


# ---------------------------------------------------------------------------
# Campos que devem ser preservados (não são PII)
# ---------------------------------------------------------------------------

_PRESERVE_FIELDS = {
    "BEGIN", "END", "VERSION", "REV", "PRODID", "UID",
    "KIND", "CATEGORIES", "TITLE", "ROLE", "X-ABLabel",
    "PHOTO", "LOGO", "SOUND", "KEY", "SOURCE", "URL",
    "BDAY", "ANNIVERSARY", "GENDER", "TZ", "GEO",
    "SORT-STRING", "CLASS", "PROFILE",
}


# ---------------------------------------------------------------------------
# Anonimização de campos vCard
# ---------------------------------------------------------------------------

def _anonymize_fn(value: str) -> str:
    """Anonimiza campo FN (Full Name)."""
    if not value.strip():
        return value
    return _fake_full_name(value)


def _anonymize_n(value: str, fake_full_name: str) -> str:
    """
    Anonimiza campo N (Structured Name).
    Formato: Sobrenome;Nome;Nomes adicionais;Prefixo;Sufixo
    Usa componentes derivados do fake_full_name para consistência.
    """
    parts = value.split(";")
    # Decompõe o nome fake em partes
    name_parts = fake_full_name.split()
    fake_last = name_parts[-1] if name_parts else _fake.last_name()
    fake_first = name_parts[0] if name_parts else _fake.first_name()
    fake_middle = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""

    result = []  # type: List[str]
    # Sobrenome
    result.append(fake_last if len(parts) > 0 and parts[0].strip() else "")
    # Nome
    result.append(fake_first if len(parts) > 1 and parts[1].strip() else "")
    # Nomes adicionais
    result.append(fake_middle if len(parts) > 2 and parts[2].strip() else "")
    # Prefixo (Sr., Sra., etc.) — preservar se existir
    result.append(parts[3] if len(parts) > 3 else "")
    # Sufixo (Jr., III, etc.) — preservar se existir
    result.append(parts[4] if len(parts) > 4 else "")

    return ";".join(result)


def _anonymize_email_field(value: str) -> str:
    """Anonimiza campo EMAIL."""
    if not value.strip():
        return value
    return _fake_email(value)


def _anonymize_tel(value: str) -> str:
    """Anonimiza campo TEL."""
    if not value.strip():
        return value
    return _fake_phone(value)


def _anonymize_adr(value: str) -> str:
    """
    Anonimiza campo ADR (Address).
    Formato: PO Box;Extended;Street;City;Region;Postal Code;Country
    """
    parts = value.split(";")
    cache_key = value.strip().lower()

    if cache_key not in _consistency_cache:
        fake_addr = _fake_address_components()
        _consistency_cache[cache_key] = ";".join([
            fake_addr["po_box"],
            fake_addr["extended"],
            fake_addr["street"],
            fake_addr["city"],
            fake_addr["region"],
            fake_addr["postal_code"],
            fake_addr["country"],
        ])

    return _consistency_cache[cache_key]


def _anonymize_org(value: str) -> str:
    """Anonimiza campo ORG."""
    if not value.strip():
        return value
    # ORG pode ter subunidades separadas por ';'
    org_parts = value.split(";")
    anon_parts = []  # type: List[str]
    for part in org_parts:
        if part.strip():
            anon_parts.append(_fake_company(part))
        else:
            anon_parts.append("")
    return ";".join(anon_parts)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def anonymize_vcf(input_path: Path) -> Tuple[Path, Path]:
    """
    Anonimiza um arquivo vCard (.vcf).

    Args:
        input_path: Caminho para o arquivo .vcf

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimização VCF: {input_path.name}")

    # --- Leitura com fallback de encoding ---
    content = None
    used_encoding = "utf-8"
    for enc in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
        try:
            content = input_path.read_text(encoding=enc)
            used_encoding = enc
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        content = input_path.read_text(encoding="utf-8", errors="replace")
        log.warning(f"Encoding não detectado para '{input_path.name}', usando UTF-8 com replace")

    # --- Parse ---
    cards = _parse_vcards(content)
    total_contacts = len(cards)
    log.info(f"VCF carregado: {total_contacts} contato(s), encoding={used_encoding}")

    if total_contacts == 0:
        log.warning("Nenhum contato encontrado no arquivo VCF")

    # --- Anonimização ---
    engine = TextAnonymizer()
    _consistency_cache.clear()

    anonymized_cards = []  # type: List[List[Tuple[str, str, str]]]
    total_fields_anonymized = 0
    fields_by_type = {}  # type: Dict[str, int]

    for card in cards:
        anon_card = []  # type: List[Tuple[str, str, str]]

        # Primeira passada: anonimizar FN para usar no N
        fn_value = ""
        fake_fn = ""
        for field_name, params, value in card:
            if field_name == "FN":
                fn_value = value
                fake_fn = _anonymize_fn(value)
                break

        for field_name, params, value in card:
            anon_value = value

            if field_name == "FN":
                anon_value = fake_fn
                total_fields_anonymized += 1
                fields_by_type["FN"] = fields_by_type.get("FN", 0) + 1

            elif field_name == "N":
                # Usa o fake_fn para manter consistência FN ↔ N
                effective_fake_fn = fake_fn if fake_fn else _fake.name()
                anon_value = _anonymize_n(value, effective_fake_fn)
                total_fields_anonymized += 1
                fields_by_type["N"] = fields_by_type.get("N", 0) + 1

            elif field_name == "EMAIL":
                anon_value = _anonymize_email_field(value)
                total_fields_anonymized += 1
                fields_by_type["EMAIL"] = fields_by_type.get("EMAIL", 0) + 1

            elif field_name == "TEL":
                anon_value = _anonymize_tel(value)
                total_fields_anonymized += 1
                fields_by_type["TEL"] = fields_by_type.get("TEL", 0) + 1

            elif field_name == "ADR":
                anon_value = _anonymize_adr(value)
                total_fields_anonymized += 1
                fields_by_type["ADR"] = fields_by_type.get("ADR", 0) + 1

            elif field_name == "ORG":
                anon_value = _anonymize_org(value)
                total_fields_anonymized += 1
                fields_by_type["ORG"] = fields_by_type.get("ORG", 0) + 1

            elif field_name == "NOTE":
                # Aplica text_engine para detectar CPF, CNPJ, nomes etc.
                anon_value = engine.anonymize(value)
                total_fields_anonymized += 1
                fields_by_type["NOTE"] = fields_by_type.get("NOTE", 0) + 1

            elif field_name.upper() in _PRESERVE_FIELDS:
                # Preservar sem alteração
                pass

            anon_card.append((field_name, params, anon_value))

        anonymized_cards.append(anon_card)

    log.info(f"Campos anonimizados: {total_fields_anonymized} em {total_contacts} contato(s)")
    log.info(f"Campos por tipo: {fields_by_type}")

    # Log de substituições do text_engine (NOTE)
    if engine.entity_map:
        log.info(f"Entidades text_engine (NOTE): {len(engine.entity_map)} ocorrências únicas")
        for i, (token, _original) in enumerate(list(engine.entity_map.items())[:5]):
            log.info(f"  Substituição #{i+1}: -> '{token}'")

    # --- Salvar arquivo anonimizado (.vcf) ---
    output_text = _serialize_vcards(anonymized_cards)
    anon_filename = f"anon_{stem}_{timestamp}.vcf"
    anon_path = ANONYMIZED_DIR / anon_filename
    anon_path.write_text(output_text, encoding="utf-8")
    log.info(f"VCF anonimizado salvo: {anon_path}")

    # --- Salvar mapa ---
    # Combina entidades do cache de consistência e do text_engine
    all_entities = {}  # type: Dict[str, str]
    for normalized_key, fake_val in _consistency_cache.items():
        all_entities[fake_val] = normalized_key
    for token, original in engine.entity_map.items():
        all_entities[token] = original

    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "contato",
        "formato_original": ".vcf",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_contatos": total_contacts,
        "entidades": all_entities,
        "estatisticas": {
            "campos_anonimizados": total_fields_anonymized,
            "campos_por_tipo": fields_by_type,
            "pessoas_substituidas": engine._counters["pessoa"],
            "empresas_substituidas": engine._counters["empresa"],
            "total_entidades": len(all_entities),
        },
    }

    map_filename = f"map_{stem}_{timestamp}.json"
    map_path = MAPS_DIR / map_filename
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa salvo: {map_path}")
    log.info(
        f"Anonimização concluída: {total_contacts} contato(s), "
        f"{total_fields_anonymized} campo(s) anonimizado(s)."
    )

    return anon_path, map_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Anonimizador de contatos VCF (vCard)"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo VCF a anonimizar")
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".vcf":
        log.error(f"Formato não suportado: {input_path.suffix}. Use .vcf")
        sys.exit(1)

    anon_path, map_path = anonymize_vcf(input_path)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
