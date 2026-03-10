"""
PSA - Privacy Shield Agent
Script: anonymizer.py
Responsável: PSA Guardião

Anonimiza planilhas CSV e XLSX:
  - Detecta automaticamente colunas sensíveis
  - Substitui dados reais por dados sintéticos (Faker)
  - Aplica text_engine em colunas de texto livre (C-02)
  - Renomeia colunas para códigos genéricos (COL_A, COL_B, ...)
  - Valida e BLOQUEIA saída em caso de vazamento (C-01)
  - Salva arquivo anonimizado em data/anonymized/
  - Salva mapa de correspondência em data/maps/

Uso:
  python3 scripts/anonymizer.py <caminho_do_arquivo> [--sample <n_linhas>]

Exemplos:
  python3 scripts/anonymizer.py data/real/clientes.xlsx
  python3 scripts/anonymizer.py data/real/folha.csv --sample 50
"""

import os
import sys
import json
import re
import string
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANONYMIZED_DIR = BASE_DIR / "data" / "anonymized"
MAPS_DIR = BASE_DIR / "data" / "maps"
LOGS_DIR = BASE_DIR / "logs"

for d in (ANONYMIZED_DIR, MAPS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA-Guardião] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

fake = Faker("pt_BR")
# Seed aleatório baseado em entropia do SO (não determinístico)
Faker.seed(int.from_bytes(os.urandom(8), "big"))

sys.path.insert(0, str(BASE_DIR / "scripts"))

# ---------------------------------------------------------------------------
# Detecção de colunas sensíveis
# ---------------------------------------------------------------------------

# H-02: Keywords expandidas com documentos, financeiros e familiares
SENSITIVE_KEYWORDS: Dict[str, str] = {
    "nome":          "name",
    "name":          "name",
    "nome_mae":      "name",
    "nome_pai":      "name",
    "mae":           "name",
    "pai":           "name",
    "razao":         "company",
    "empresa":       "company",
    "company":       "company",
    "fantasia":      "company",
    "cpf":           "cpf",
    "cnpj":          "cnpj",
    "rg":            "rg",
    "cnh":           "cnh",
    "titulo_eleitor":"id_number",
    "titulo":        "id_number",
    "pis":           "id_number",
    "pasep":         "id_number",
    "nis":           "id_number",
    "nit":           "id_number",
    "ctps":          "id_number",
    "sus":           "id_number",
    "passaporte":    "id_number",
    "email":         "email",
    "e-mail":        "email",
    "mail":          "email",
    "telefone":      "phone",
    "celular":       "phone",
    "fone":          "phone",
    "phone":         "phone",
    "tel":           "phone",
    "endereco":      "address",
    "endereço":      "address",
    "address":       "address",
    "logradouro":    "address",
    "rua":           "street",
    "avenida":       "street",
    "bairro":        "neighborhood",
    "cidade":        "city",
    "municipio":     "city",
    "estado":        "state",
    "uf":            "state",
    "cep":           "zipcode",
    "salario":       "salary",
    "salário":       "salary",
    "salary":        "salary",
    "remuneracao":   "salary",
    "remuneração":   "salary",
    "vencimento":    "salary",
    "bruto":         "salary",
    "liquido":       "salary",
    "líquido":       "salary",
    "valor":         "amount",
    "amount":        "amount",
    "receita":       "amount",
    "faturamento":   "amount",
    "despesa":       "amount",
    "custo":         "amount",
    "debito":        "amount",
    "credito":       "amount",
    "saldo":         "amount",
    "desconto":      "amount",
    "gratificacao":  "amount",
    "adicional":     "amount",
    "abono":         "amount",
    "auxilio":       "amount",
    "subsidio":      "amount",
    "conta":         "account",
    "agencia":       "agency",
    "agência":       "agency",
    "banco":         "bank",
    "cartao":        "card",
    "cartão":        "card",
    "pix":           "pix",
    "nascimento":    "birthdate",
    "nasc":          "birthdate",
    "birthdate":     "birthdate",
    "birth":         "birthdate",
    "idade":         "age",
    "age":           "age",
    "senha":         "password",
    "password":      "password",
    "token":         "token",
    "chave":         "key",
    "processo":      "process_number",
    "matricula":     "id_number",
    "matrícula":     "id_number",
    "placa":         "id_number",
    "chassi":        "id_number",
    "renavam":       "id_number",
    "latitude":      "coordinate",
    "longitude":     "coordinate",
    "lat":           "coordinate",
    "lng":           "coordinate",
    "lon":           "coordinate",
}

# H-02: Keywords curtas que exigem match exato (não parcial)
_SHORT_EXACT_KEYWORDS: Set[str] = {"rg", "uf", "tel", "cpf", "cep", "pis", "nis", "nit", "mae", "pai", "lat", "lng", "lon"}


def detect_sensitivity(col_name: str) -> Optional[str]:
    """Retorna o tipo sensível detectado ou None se não for sensível."""
    normalized = col_name.lower().strip()
    clean = normalized.replace("-", "").replace("_", "").replace(" ", "")
    # Primeiro tenta match exato (prioridade)
    for keyword, kind in SENSITIVE_KEYWORDS.items():
        kw = keyword.replace("-", "").replace("_", "").replace(" ", "")
        if kw == clean:
            return kind
    # Match parcial: keywords com 4+ chars
    for keyword, kind in SENSITIVE_KEYWORDS.items():
        kw = keyword.replace("-", "").replace("_", "").replace(" ", "")
        if len(kw) >= 4 and kw in clean:
            return kind
    # H-02: Keywords curtas — match por word boundary no nome original
    # Ex: "num_rg" → encontra "rg"; "cargo" → não encontra "rg"
    words = set(re.split(r'[-_\s]+', normalized))
    for short_kw in _SHORT_EXACT_KEYWORDS:
        if short_kw in words:
            kw_clean = short_kw.replace("-", "").replace("_", "")
            if kw_clean in SENSITIVE_KEYWORDS:
                return SENSITIVE_KEYWORDS[kw_clean]
    return None


# ---------------------------------------------------------------------------
# Heurística de texto livre (C-02)
# ---------------------------------------------------------------------------

def _is_freetext_column(series: pd.Series) -> bool:
    """Detecta se uma coluna contém texto livre que pode ter PII."""
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    avg_len = sample.astype(str).str.len().mean()
    # Texto livre tende a ter comprimento médio > 20 caracteres
    if avg_len < 20:
        return False
    # Verifica se tem espaços (indicativo de texto livre vs códigos)
    has_spaces = sample.astype(str).str.contains(r'\s').mean()
    return has_spaces > 0.5


# ---------------------------------------------------------------------------
# Geradores de dados sintéticos
# ---------------------------------------------------------------------------

# Cache para manter consistência: mesmo valor real → mesmo valor fake
_cache: Dict[str, str] = {}


def _cached(real_value: str, generator_fn) -> str:
    """Garante que o mesmo valor real sempre gere o mesmo valor fake."""
    # SHA-256 em vez de MD5 (M-07)
    key = hashlib.sha256(str(real_value).encode()).hexdigest()
    if key not in _cache:
        _cache[key] = generator_fn()
    return _cache[key]


def _fake_cpf() -> str:
    digits = [fake.random_int(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(digits) + 1 - i) * v for i, v in enumerate(digits))
        d = (s * 10 % 11) % 10
        digits.append(d)
    return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*digits)


def _fake_cnpj() -> str:
    def calc(digits, weights):
        s = sum(d * w for d, w in zip(digits, weights))
        r = s % 11
        return 0 if r < 2 else 11 - r
    base = [fake.random_int(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    d1 = calc(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc(base + [d1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    n = base + [d1, d2]
    return "{}{}.{}{}{}.{}{}{}/{}{}{}{}-{}{}".format(*n)


def _anonymize_amount(value) -> str:
    """Mantém a ordem de grandeza mas troca o valor exato."""
    try:
        clean = re.sub(r"[R$\s\.]", "", str(value)).replace(",", ".")
        num = float(clean)
        if num == 0:
            return "0"
        variation = fake.random.uniform(0.85, 1.15)
        new_val = num * variation
        return f"{new_val:.2f}"
    except (ValueError, TypeError):
        return str(value)


def _anonymize_coordinate(value) -> str:
    """Desloca coordenada geográfica aleatoriamente (±0.05 graus ~5km)."""
    try:
        num = float(str(value).replace(",", "."))
        offset = fake.random.uniform(-0.05, 0.05)
        return f"{num + offset:.6f}"
    except (ValueError, TypeError):
        return str(value)


GENERATORS: Dict[str, object] = {
    "name":           lambda v: _cached(v, fake.name),
    "company":        lambda v: _cached(v, fake.company),
    "cpf":            lambda v: _cached(v, _fake_cpf),
    "cnpj":           lambda v: _cached(v, _fake_cnpj),
    "rg":             lambda v: _cached(v, lambda: str(fake.random_number(digits=9))),
    "cnh":            lambda v: _cached(v, lambda: str(fake.random_number(digits=11))),
    "email":          lambda v: _cached(v, fake.email),
    "phone":          lambda v: _cached(v, fake.phone_number),
    "address":        lambda v: _cached(v, fake.address),
    "street":         lambda v: _cached(v, fake.street_name),
    "neighborhood":   lambda v: _cached(v, fake.bairro),
    "city":           lambda v: _cached(v, fake.city),
    "state":          lambda v: _cached(v, fake.estado_sigla),
    "zipcode":        lambda v: _cached(v, fake.postcode),
    "birthdate":      lambda v: _cached(v, lambda: str(fake.date_of_birth(minimum_age=18, maximum_age=70))),
    "age":            lambda v: str(fake.random_int(18, 70)),
    "password":       lambda v: _cached(v, lambda: fake.password(length=12)),
    "token":          lambda v: _cached(v, lambda: fake.sha256()),
    "key":            lambda v: _cached(v, lambda: fake.sha1()),
    "process_number": lambda v: _cached(v, lambda: f"{fake.random_number(7)}-{fake.random_number(2)}.{fake.random_number(4)}.{fake.random_int(1,9)}.{fake.random_int(1000,9999)}.{fake.random_number(4)}"),
    "id_number":      lambda v: _cached(v, lambda: str(fake.random_number(digits=8))),
    "account":        lambda v: _cached(v, lambda: str(fake.random_number(digits=6))),
    "agency":         lambda v: _cached(v, lambda: str(fake.random_number(digits=4))),
    "bank":           lambda v: _cached(v, fake.bank),
    "card":           lambda v: _cached(v, lambda: fake.credit_card_number()),
    "pix":            lambda v: _cached(v, fake.email),
    "salary":         _anonymize_amount,
    "amount":         _anonymize_amount,
    "coordinate":     _anonymize_coordinate,
}


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _col_code(index: int) -> str:
    """Converte índice numérico em código de coluna: 0→COL_A, 25→COL_Z, 26→COL_AA."""
    result = ""
    n = index
    while True:
        result = string.ascii_uppercase[n % 26] + result
        n = n // 26 - 1
        if n < 0:
            break
    return f"COL_{result}"


def _anonymize_cell(value, kind: str) -> str:
    """Anonimiza um valor de célula conforme o tipo sensível."""
    if pd.isna(value) or str(value).strip() == "":
        return value
    generator = GENERATORS.get(kind)
    if generator:
        return generator(value)
    return str(value)


# ---------------------------------------------------------------------------
# Exceção de vazamento (C-01)
# ---------------------------------------------------------------------------

class LeakageError(Exception):
    """Exceção levantada quando dados reais vazam para o arquivo anonimizado."""
    pass


# ---------------------------------------------------------------------------
# Função principal de anonimização
# ---------------------------------------------------------------------------

def anonymize_spreadsheet(
    input_path: Path,
    sample_size: int = 100,
) -> Tuple[Path, Path]:
    """
    Anonimiza uma planilha CSV ou XLSX.

    Args:
        input_path: Caminho para o arquivo real (em data/real/)
        sample_size: Número máximo de linhas a incluir na amostra

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)

    Raises:
        LeakageError: Se dados reais vazarem para o arquivo anonimizado
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem
    suffix = input_path.suffix.lower()

    log.info(f"Iniciando anonimização: {input_path.name}")

    # --- Leitura ---
    if suffix == ".csv":
        df = None
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"):
            for sep in (",", ";", "\t", "|"):
                try:
                    candidate = pd.read_csv(input_path, dtype=str, encoding=enc, sep=sep)
                    # Descarta se resultou em coluna única (separador errado)
                    if len(candidate.columns) > 1:
                        df = candidate
                        log.info(f"Encoding: {enc} | Separador: '{sep}'")
                        break
                except Exception:
                    continue
            if df is not None:
                break
        if df is None:
            raise ValueError("Não foi possível ler o CSV. Verifique encoding e separador.")
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(input_path, dtype=str)
    else:
        raise ValueError(f"Formato não suportado: {suffix}. Use CSV ou XLSX.")

    total_rows = len(df)
    log.info(f"Arquivo carregado: {total_rows} linhas, {len(df.columns)} colunas")

    # --- Amostragem ---
    if total_rows > sample_size:
        df_sample = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        log.info(f"Amostra selecionada: {sample_size} de {total_rows} linhas")
    else:
        df_sample = df.copy()
        log.info(f"Usando todas as {total_rows} linhas (abaixo do limite de {sample_size})")

    # --- Detecção de colunas sensíveis ---
    col_types: Dict[str, Optional[str]] = {}
    for col in df_sample.columns:
        kind = detect_sensitivity(col)
        col_types[col] = kind
        if kind:
            log.info(f"  Coluna sensível detectada: '{col}' -> tipo '{kind}'")
        else:
            log.info(f"  Coluna não-sensível: '{col}'")

    # --- Renomeação de colunas ---
    col_rename_map: Dict[str, str] = {}
    for i, col in enumerate(df_sample.columns):
        col_rename_map[col] = _col_code(i)

    df_anon = df_sample.rename(columns=col_rename_map)

    # --- Anonimização dos valores sensíveis ---
    for original_col, kind in col_types.items():
        if kind is None:
            continue
        new_col = col_rename_map[original_col]
        log.info(f"  Anonimizando coluna: {new_col} (tipo={kind})")
        df_anon[new_col] = df_sample[original_col].apply(
            lambda v: _anonymize_cell(v, kind)
        )

    # --- C-02: Aplica text_engine em colunas de texto livre não-sensíveis ---
    from text_engine import TextAnonymizer
    text_eng = TextAnonymizer()
    freetext_cols: List[str] = []

    for original_col, kind in col_types.items():
        if kind is not None:
            continue  # já anonimizada
        new_col = col_rename_map[original_col]
        if _is_freetext_column(df_sample[original_col]):
            freetext_cols.append(original_col)
            log.info(f"  Texto livre detectado em '{original_col}' -> aplicando text_engine")
            df_anon[new_col] = df_sample[original_col].apply(
                lambda v: text_eng.anonymize(str(v)) if pd.notna(v) and str(v).strip() else v
            )

    if freetext_cols:
        log.info(f"  text_engine aplicado em {len(freetext_cols)} coluna(s) de texto livre")

    # --- Validação de segurança (C-01: BLOQUEIA em caso de vazamento) ---
    anon_filename = f"anon_{stem}_{timestamp}{suffix}"
    anon_path = ANONYMIZED_DIR / anon_filename

    _validate_no_leakage(df_sample, df_anon, col_types, col_rename_map, anon_path)

    # --- Salvar arquivo anonimizado ---
    if suffix == ".csv":
        df_anon.to_csv(anon_path, index=False)
    else:
        df_anon.to_excel(anon_path, index=False)

    log.info(f"Arquivo anonimizado salvo: {anon_path}")

    # --- Salvar mapa de correspondência ---
    map_data = {
        "timestamp": datetime.now().isoformat(),
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_linhas_original": total_rows,
        "total_linhas_amostra": len(df_anon),
        "colunas": {
            col_rename_map[col]: {
                "nome_original": col,
                "tipo_sensivel": kind,
                "anonimizada": kind is not None,
                "texto_livre": col in freetext_cols,
            }
            for col, kind in col_types.items()
        },
    }

    map_filename = f"map_{stem}_{timestamp}.json"
    map_path = MAPS_DIR / map_filename

    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

    log.info(f"Mapa de correspondência salvo: {map_path}")

    # --- Resumo ---
    sensitive_count = sum(1 for k in col_types.values() if k is not None)
    log.info(
        f"Anonimização concluída: {sensitive_count}/{len(df_sample.columns)} colunas "
        f"sensíveis + {len(freetext_cols)} texto livre, {len(df_anon)} linhas na amostra."
    )

    return anon_path, map_path


def _validate_no_leakage(
    df_original: pd.DataFrame,
    df_anon: pd.DataFrame,
    col_types: Dict[str, Optional[str]],
    col_rename_map: Dict[str, str],
    anon_path: Path,
):
    """
    C-01: Verificação de segurança que BLOQUEIA a saída em caso de vazamento.
    Se dados reais de colunas sensíveis aparecerem no arquivo anonimizado,
    deleta o arquivo (se existir) e levanta LeakageError.
    """
    leaks: List[Tuple[str, str, List[str]]] = []
    for original_col, kind in col_types.items():
        if kind is None:
            continue
        new_col = col_rename_map[original_col]
        original_values = set(df_original[original_col].dropna().astype(str))
        anon_values = set(df_anon[new_col].dropna().astype(str))
        overlap = original_values & anon_values
        # Ignora valores genéricos que podem coincidir por acaso
        overlap = {v for v in overlap if len(v.strip()) > 3}
        if overlap:
            leaks.append((original_col, kind, list(overlap)[:5]))

    if leaks:
        # C-01: BLOQUEIA — deleta arquivo se existir e levanta exceção
        if anon_path.exists():
            anon_path.unlink()
            log.error(f"ARQUIVO DELETADO por vazamento: {anon_path}")

        leak_summary = []
        for col, kind, examples in leaks:
            # Log sem expor os valores reais — apenas contagem
            leak_summary.append(f"Coluna '{col}' (tipo={kind}): {len(examples)} valor(es) vazado(s)")

        msg = (
            "VAZAMENTO DETECTADO — SAÍDA BLOQUEADA.\n"
            + "\n".join(f"  - {s}" for s in leak_summary)
            + "\nNenhum arquivo foi gerado. Corrija o gerador antes de prosseguir."
        )
        log.error(msg)
        raise LeakageError(msg)
    else:
        log.info("Validação de segurança: PASSOU — nenhum vazamento detectado.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardião — Anonimizador de planilhas CSV/XLSX"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo a anonimizar")
    parser.add_argument(
        "--sample",
        type=int,
        default=100,
        metavar="N",
        help="Número máximo de linhas na amostra (padrão: 100)",
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo não encontrado: {input_path}")
        sys.exit(1)

    try:
        anon_path, map_path = anonymize_spreadsheet(input_path, sample_size=args.sample)
    except LeakageError:
        log.error("Operação abortada por vazamento de dados.")
        sys.exit(2)

    print("\n" + "=" * 60)
    print("PSA GUARDIÃO — ANONIMIZAÇÃO CONCLUÍDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado : {anon_path}")
    print(f"  Mapa de correspondência: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
