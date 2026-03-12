"""
PSA - Privacy Shield Agent
Script: anonymize_parquet.py
Responsavel: PSA Guardiao

Anonimiza arquivos Parquet:
  - Detecta automaticamente colunas sensiveis (mesma logica de anonymizer.py)
  - Substitui dados reais por dados sinteticos (Faker)
  - Aplica text_engine em colunas de texto livre (C-02)
  - Renomeia colunas para codigos genericos (COL_A, COL_B, ...)
  - Valida e BLOQUEIA saida em caso de vazamento (C-01)
  - Salva arquivo anonimizado em data/anonymized/ (.parquet)
  - Salva mapa de correspondencia em data/maps/

Uso:
  python3 scripts/anonymize_parquet.py <caminho_do_arquivo> [--sample <n_linhas>]

Exemplos:
  python3 scripts/anonymize_parquet.py data/real/clientes.parquet
  python3 scripts/anonymize_parquet.py data/real/folha.parquet --sample 50
"""

import os
import sys
import json
import re
import string
import hashlib
import argparse
import logging
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
ANONYMIZED_DIR = BASE_DIR / "data" / "anonymized"
MAPS_DIR = BASE_DIR / "data" / "maps"
LOGS_DIR = BASE_DIR / "logs"

for d in (ANONYMIZED_DIR, MAPS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PSA-Guardiao] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "psa_guardiao.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

fake = Faker("pt_BR")
# Seed aleatorio baseado em entropia do SO (nao deterministico)
Faker.seed(int.from_bytes(os.urandom(8), "big"))
random.seed(int.from_bytes(os.urandom(8), "big"))

sys.path.insert(0, str(BASE_DIR / "scripts"))

from text_engine import TextAnonymizer

# ---------------------------------------------------------------------------
# Deteccao de colunas sensiveis (mesma logica de anonymizer.py)
# ---------------------------------------------------------------------------

SENSITIVE_KEYWORDS = {
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
    "preco":         "amount",
    "preço":         "amount",
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
    "chave_pix":     "pix",
    "chavepix":      "pix",
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
    "carteirinha":   "id_number",
    "carteira":      "id_number",
    "registro":      "id_number",
    "inscricao":     "id_number",
    "inscrição":     "id_number",
    "gestor":        "name",
    "responsavel":   "name",
    "responsável":   "name",
    "supervisor":    "name",
    "coordenador":   "name",
    "gerente":       "name",
    "diretor":       "name",
    "placa":         "id_number",
    "chassi":        "id_number",
    "renavam":       "id_number",
    "latitude":      "coordinate",
    "longitude":     "coordinate",
    "lat":           "coordinate",
    "lng":           "coordinate",
    "lon":           "coordinate",
    "ip":            "ip",
    "ip_acesso":     "ip",
    "ip_address":    "ip",
    "ip_origem":     "ip",
}  # type: Dict[str, str]

# Keywords curtas que exigem match exato (nao parcial)
_SHORT_EXACT_KEYWORDS = {
    "rg", "uf", "tel", "cpf", "cep", "pis", "nis", "nit", "mae", "pai",
    "lat", "lng", "lon", "ip",
}  # type: Set[str]

# ---------------------------------------------------------------------------
# Whitelist de padroes de colunas nao-sensiveis
# ---------------------------------------------------------------------------

_NON_SENSITIVE_PREFIXES = [
    "cod_", "codigo_", "código_",
    "descricao_", "descrição_",
    "situacao_", "situação_",
    "regime_", "jornada_",
    "nivel_", "nível_",
    "referencia_", "referência_",
    "padrao_", "padrão_",
    "sigla_", "tipo_", "classe_",
    "diploma_", "documento_",
    "opcao_", "opção_",
    "data_ingresso", "data_nomeacao", "data_nomeação",
    "data_diploma", "data_inicio", "data_início",
    "data_termino", "data_término", "data_posse",
    "data_publicacao", "data_publicação", "data_criacao",
    "data_atualizacao", "data_cadastro", "data_registro",
    "uf_",
]  # type: List[str]

_NON_SENSITIVE_EXACT = {
    "ano", "mes", "mês", "dia", "semestre", "trimestre", "bimestre",
    "id", "seq", "sequencia", "orgao", "órgão", "uorg",
    "funcao", "função", "atividade",
    "user_id", "usuario_id", "client_id", "order_id", "transaction_id",
    "event_id", "request_id", "session_id",
    "status", "type", "category", "categoria",
}  # type: Set[str]


def detect_sensitivity(col_name: str) -> Optional[str]:
    """
    Retorna o tipo sensivel detectado, None se sem match, ou False se
    explicitamente nao-sensivel (whitelist). False impede a heuristica
    de conteudo de rodar para esta coluna.
    """
    normalized = str(col_name).lower().strip()
    # Ignora colunas geradas pelo pandas (Unnamed: 0, etc.)
    if re.match(r'^unnamed\s*:\s*\d+$', normalized):
        return False
    # Ignora colunas que sao apenas numeros (anos, periodos: 2001, 2024)
    if re.match(r'^\d+$', normalized):
        return False
    # Ignora colunas de periodo trimestral (1Q23, 4Q25, etc.)
    if re.match(r'^[1-4]q\d{2}$', normalized):
        return False

    # Whitelist de padroes nao-sensiveis (antes das keywords)
    for prefix in _NON_SENSITIVE_PREFIXES:
        if normalized.startswith(prefix):
            return False
    # Match exato por palavras (separadas por _ ou -)
    col_words = set(re.split(r'[-_\s]+', normalized))
    if col_words & _NON_SENSITIVE_EXACT:
        # Excecao: se a coluna e exatamente um nome sensivel conhecido,
        # a keyword sensivel prevalece
        clean = normalized.replace("-", "").replace("_", "").replace(" ", "")
        for keyword in SENSITIVE_KEYWORDS:
            kw = keyword.replace("-", "").replace("_", "").replace(" ", "")
            if kw == clean:
                break  # match exato com keyword sensivel - nao ignorar
        else:
            return False  # nenhum match exato - e nao-sensivel

    clean = normalized.replace("-", "").replace("_", "").replace(" ", "")
    # Match exato (prioridade)
    for keyword, kind in SENSITIVE_KEYWORDS.items():
        kw = keyword.replace("-", "").replace("_", "").replace(" ", "")
        if kw == clean:
            return kind
    # Match parcial com word boundary
    col_words_clean = set(re.split(r'[-_\s]+', normalized))
    for keyword, kind in SENSITIVE_KEYWORDS.items():
        kw_clean = keyword.replace("-", "").replace("_", "").replace(" ", "")
        if len(kw_clean) < 4:
            continue  # keywords curtas tratadas separadamente abaixo
        for word in col_words_clean:
            if word == kw_clean:
                return kind
    # Keywords curtas - match por word boundary
    words = set(re.split(r'[-_\s]+', normalized))
    for short_kw in _SHORT_EXACT_KEYWORDS:
        if short_kw in words:
            kw_clean = short_kw.replace("-", "").replace("_", "")
            if kw_clean in SENSITIVE_KEYWORDS:
                return SENSITIVE_KEYWORDS[kw_clean]
    return None


# ---------------------------------------------------------------------------
# Heuristica de texto livre (C-02)
# ---------------------------------------------------------------------------

def _is_freetext_column(series: pd.Series) -> bool:
    """Detecta se uma coluna contem texto livre que pode ter PII."""
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    avg_len = sample.astype(str).str.len().mean()
    if avg_len < 20:
        return False
    has_spaces = sample.astype(str).str.contains(r'\s').mean()
    return has_spaces > 0.5


# ---------------------------------------------------------------------------
# Deteccao de tipo de coluna por conteudo
# ---------------------------------------------------------------------------

def detect_column_type(series: pd.Series) -> str:
    """
    Analisa o conteudo de uma coluna para determinar seu tipo real.

    Returns:
        "id_number"      - IDs numericos unicos (sem decimais, alta cardinalidade)
        "amount"         - valores financeiros (decimais, zeros, baixa cardinalidade)
        "financial_text" - texto com indicadores financeiros (R$, %, milhoes)
        "date"           - datas ou periodos (1Q23, 4Q25, 2024, etc.)
        "name"           - nomes proprios (Mixed Case, alta cardinalidade)
        "enum"           - categorias/enums (poucos valores unicos)
        "mixed"          - mistura de tipos
        "empty"          - coluna vazia ou quase vazia
    """
    sample = series.dropna().head(100)
    if len(sample) < 2:
        return "empty"

    n = len(sample)
    numeric_count = 0
    has_decimal = 0
    zero_count = 0
    financial_text_count = 0
    date_count = 0
    name_count = 0

    for val in sample.astype(str):
        val_clean = val.strip()
        if not val_clean:
            continue

        if re.match(r'^-?[\d.,]+(?:[eE][+-]?\d+)?$', val_clean.replace(" ", "")):
            numeric_count += 1
            normalized_num = val_clean.replace(".", "").replace(",", ".")
            if "," in val_clean or (
                val_clean.count(".") > 0
                and not val_clean.replace(".", "").replace("-", "").isdigit()
            ):
                has_decimal += 1
            try:
                if float(normalized_num) == 0:
                    zero_count += 1
            except ValueError:
                pass
            continue

        if re.search(
            r'R\$|US\$|%|milh[õo]|bilh[õo]|thousand|million|billion',
            val_clean, re.IGNORECASE,
        ):
            financial_text_count += 1
            continue

        if re.match(r'^[1-4]Q\d{2}$', val_clean) or re.match(r'^\d{4}$', val_clean):
            date_count += 1
            continue

        words = val_clean.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w.isalpha()):
            name_count += 1
            continue

    if n == 0:
        return "empty"

    unique_values = series.dropna().head(100).nunique()
    unique_ratio = unique_values / n if n > 0 else 1

    if numeric_count / n >= 0.5:
        is_integer_like = has_decimal < numeric_count * 0.1
        has_many_zeros = zero_count > numeric_count * 0.3
        is_high_cardinality = unique_values > n * 0.5
        if is_integer_like and is_high_cardinality and not has_many_zeros:
            return "id_number"
        return "amount"
    if financial_text_count / n >= 0.3:
        return "financial_text"
    if date_count / n >= 0.5:
        return "date"
    if name_count / n >= 0.5:
        if unique_values < 10 or unique_ratio < 0.1:
            return "enum"
        return "name"
    if (numeric_count + financial_text_count) / n >= 0.5:
        return "amount"
    return "mixed"


# ---------------------------------------------------------------------------
# Geradores de dados sinteticos
# ---------------------------------------------------------------------------

_cache = {}  # type: Dict[str, str]


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
    """Mantem a ordem de grandeza mas troca o valor exato (variacao +-15%)."""
    try:
        s = str(value).strip()
        if s.lower() in ("nan", "none", ""):
            return value
        try:
            num = float(s)
            if num != num:  # NaN check
                return value
        except ValueError:
            # Formato brasileiro: R$ 1.234,56 ou 1.234.567,89
            clean = re.sub(r"[R$\s]", "", s)
            if "," in clean:
                clean = clean.replace(".", "").replace(",", ".")
            num = float(clean)
        if num == 0:
            return "0"
        original_str = s
        if abs(num) < 0.1:
            offset = fake.random.uniform(0.01, 0.05)
            new_val = num + (offset if num >= 0 else -offset)
            return f"{new_val:.2f}"
        # Garante que o resultado nunca seja igual ao original (evita C-01)
        for _ in range(10):
            variation = fake.random.uniform(0.85, 1.15)
            new_val = num * variation
            if f"{new_val:.2f}" != original_str:
                return f"{new_val:.2f}"
        # Fallback: offset aditivo
        new_val = num + (abs(num) * 0.20)
        return f"{new_val:.2f}"
    except (ValueError, TypeError):
        return _cached(str(value), lambda: f"Item_{fake.random_number(digits=4)}")


def _anonymize_coordinate(value) -> str:
    """Desloca coordenada geografica aleatoriamente (+-0.05 graus ~5km)."""
    try:
        num = float(str(value).replace(",", "."))
        offset = fake.random.uniform(-0.05, 0.05)
        return f"{num + offset:.6f}"
    except (ValueError, TypeError):
        return str(value)


def _anonymize_date(value) -> str:
    """Desloca data por um intervalo aleatorio de -30 a +30 dias."""
    if pd.isna(value) or str(value).strip() == "":
        return value
    s = str(value).strip()
    # Tenta formatos comuns de data
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y%m%d",
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(s, fmt)
            shift_days = random.randint(-30, 30)
            new_dt = dt + timedelta(days=shift_days)
            return new_dt.strftime(fmt)
        except ValueError:
            continue
    # Se nenhum formato casar, tenta como pandas Timestamp
    try:
        ts = pd.Timestamp(value)
        if pd.notna(ts):
            shift_days = random.randint(-30, 30)
            new_ts = ts + pd.Timedelta(days=shift_days)
            return str(new_ts)
    except Exception:
        pass
    return s


def _fake_pix(real_value) -> str:
    """Gera chave PIX fake do mesmo tipo da original."""
    v = str(real_value).strip()
    if re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', v):
        return _fake_cpf()
    if "@" in v:
        return fake.email()
    if re.match(r'^[\(\+\d][\d\s\(\)\-\+]+$', v) and len(re.sub(r'\D', '', v)) >= 10:
        return fake.phone_number()
    # Chave aleatoria (EVP)
    return fake.uuid4()


GENERATORS = {
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
    "id_number":      lambda v: _cached(v, lambda: str(fake.random_number(digits=max(len(re.sub(r'\D', '', str(v))), 6)))),
    "account":        lambda v: _cached(v, lambda: str(fake.random_number(digits=6))),
    "agency":         lambda v: _cached(v, lambda: str(fake.random_number(digits=4))),
    "bank":           lambda v: _cached(v, lambda: f"Banco {fake.last_name()} ({fake.random_number(digits=3):03d})"),
    "card":           lambda v: _cached(v, lambda: fake.credit_card_number()),
    "pix":            lambda v: _cached(v, lambda: _fake_pix(v)),
    "ip":             lambda v: _cached(v, fake.ipv4),
    "salary":         _anonymize_amount,
    "amount":         _anonymize_amount,
    "coordinate":     _anonymize_coordinate,
}  # type: Dict[str, object]


# ---------------------------------------------------------------------------
# Funcoes auxiliares
# ---------------------------------------------------------------------------

def _col_code(index: int) -> str:
    """Converte indice numerico em codigo de coluna: 0->COL_A, 25->COL_Z, 26->COL_AA."""
    result = ""
    n = index
    while True:
        result = string.ascii_uppercase[n % 26] + result
        n = n // 26 - 1
        if n < 0:
            break
    return f"COL_{result}"


def _anonymize_cell(value, kind: str) -> str:
    """Anonimiza um valor de celula conforme o tipo sensivel."""
    if pd.isna(value) or str(value).strip() == "":
        return value
    generator = GENERATORS.get(kind)
    if generator:
        return generator(value)
    return str(value)


# ---------------------------------------------------------------------------
# Excecao de vazamento (C-01)
# ---------------------------------------------------------------------------

class LeakageError(Exception):
    """Excecao levantada quando dados reais vazam para o arquivo anonimizado."""
    pass


# ---------------------------------------------------------------------------
# Amostragem inteligente
# ---------------------------------------------------------------------------

def calculate_sample_size(n_rows: int) -> int:
    """
    Calcula o tamanho ideal da amostra com base no total de linhas.

    | N linhas        | Amostra           | Regra                           |
    |-----------------|-------------------|---------------------------------|
    | N <= 30         | 100% (N)          | Arquivo pequeno, manda tudo     |
    | 31 a 100        | 50% de N (min 30) | Reduz mas mantem representativ. |
    | 101 a 1.000     | 100               | Padrao                          |
    | 1.001 a 10.000  | 100               | Idem                            |
    | 10.001 a 100.000| 150               | Arquivo grande                  |
    | 100.001+        | 200               | Maximo recomendado              |
    """
    if n_rows <= 30:
        return n_rows
    elif n_rows <= 100:
        return max(30, n_rows // 2)
    elif n_rows <= 10000:
        return 100
    elif n_rows <= 100000:
        return 150
    else:
        return 200


# ---------------------------------------------------------------------------
# Validacao anti-vazamento (C-01)
# ---------------------------------------------------------------------------

def _validate_no_leakage(
    df_original: pd.DataFrame,
    df_anon: pd.DataFrame,
    col_types: Dict[str, Optional[str]],
    col_rename_map: Dict[str, str],
    anon_path: Path,
) -> None:
    """
    C-01: Verificacao de seguranca que BLOQUEIA a saida em caso de vazamento.
    Se dados reais de colunas sensiveis aparecerem no arquivo anonimizado,
    deleta o arquivo (se existir) e levanta LeakageError.
    """
    # Tipos que usam variacao numerica e podem coincidir com o original
    _SKIP_LEAKAGE_TYPES = {"amount", "salary", "coordinate", "age", "date"}

    leaks = []  # type: List[Tuple[str, str, List[str]]]
    for original_col, kind in col_types.items():
        if kind is None:
            continue
        if kind in _SKIP_LEAKAGE_TYPES:
            continue  # variacao +-15% pode gerar mesmo valor formatado
        new_col = col_rename_map[original_col]
        # Comparacao LINHA-A-LINHA: detecta se o mesmo indice manteve o valor
        col_leaks = []
        for idx in df_original.index:
            if idx not in df_anon.index:
                continue
            orig_val = (
                str(df_original.at[idx, original_col])
                if pd.notna(df_original.at[idx, original_col])
                else ""
            )
            anon_val = (
                str(df_anon.at[idx, new_col])
                if pd.notna(df_anon.at[idx, new_col])
                else ""
            )
            if orig_val == anon_val and len(orig_val.strip()) > 3:
                col_leaks.append(orig_val)
        if col_leaks:
            leaks.append((original_col, kind, col_leaks[:5]))

    if leaks:
        # C-01: BLOQUEIA - deleta arquivo se existir e levanta excecao
        if anon_path.exists():
            anon_path.unlink()
            log.error(f"ARQUIVO DELETADO por vazamento: {anon_path}")

        leak_summary = []
        for col, kind, examples in leaks:
            # Log sem expor os valores reais - apenas contagem
            leak_summary.append(
                f"Coluna '{col}' (tipo={kind}): {len(examples)} valor(es) vazado(s)"
            )

        msg = (
            "VAZAMENTO DETECTADO - SAIDA BLOQUEADA.\n"
            + "\n".join(f"  - {s}" for s in leak_summary)
            + "\nNenhum arquivo foi gerado. Corrija o gerador antes de prosseguir."
        )
        log.error(msg)
        raise LeakageError(msg)
    else:
        log.info("Validacao de seguranca: PASSOU - nenhum vazamento detectado.")


# ---------------------------------------------------------------------------
# Deteccao de colunas de data no DataFrame
# ---------------------------------------------------------------------------

def _is_date_column(series: pd.Series) -> bool:
    """Verifica se uma coluna contem datas (datetime64 ou strings parseaveais)."""
    # Parquet preserva tipos nativos; datetime64 e deteccao direta
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    # Tenta parsear amostra como data
    sample = series.dropna().head(20)
    if sample.empty:
        return False
    parsed = 0
    for val in sample.astype(str):
        try:
            pd.Timestamp(val)
            parsed += 1
        except Exception:
            pass
    return parsed / len(sample) >= 0.7


# ---------------------------------------------------------------------------
# Funcao principal de anonimizacao
# ---------------------------------------------------------------------------

def anonymize_parquet(
    input_path: Path,
    sample_size: Optional[int] = None,
) -> Tuple[Path, Path]:
    """
    Anonimiza um arquivo Parquet.

    Args:
        input_path: Caminho para o arquivo Parquet em data/real/
        sample_size: Numero de linhas na amostra.
                     None = amostragem inteligente automatica.
                     Valor explicito = sobrescreve a logica automatica.

    Returns:
        Tuple (caminho_anonimizado, caminho_mapa)

    Raises:
        LeakageError: Se dados reais vazarem para o arquivo anonimizado
    """
    input_path = Path(input_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = input_path.stem

    log.info(f"Iniciando anonimizacao Parquet: {input_path.name}")

    # --- Leitura ---
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        log.error(f"Erro ao ler Parquet: {e}")
        raise ValueError(f"Nao foi possivel ler o arquivo Parquet: {e}")

    total_rows = len(df)
    total_cols = len(df.columns)
    log.info(f"Arquivo carregado: {total_rows} linhas, {total_cols} colunas")

    # --- Amostragem inteligente ---
    if sample_size is not None:
        # Usuario informou --sample explicitamente: usa o valor dele
        effective_sample = min(sample_size, total_rows)
        log.info(f"Amostragem manual: --sample {sample_size} (usuario)")
    else:
        # Amostragem automatica baseada no tamanho do arquivo
        effective_sample = calculate_sample_size(total_rows)
        log.info(
            f"Amostragem inteligente: {effective_sample} linhas calculadas "
            f"para N={total_rows}"
        )

    pct_sent = (effective_sample / total_rows * 100) if total_rows > 0 else 100
    pct_saved = 100 - pct_sent

    if effective_sample >= total_rows:
        df_sample = df.copy()
        log.warning(
            f"Arquivo pequeno - enviando todas as {total_rows} linhas "
            f"(100% do arquivo)"
        )
    else:
        df_sample = df.sample(
            n=effective_sample, random_state=42,
        ).reset_index(drop=True)
        log.info(
            f"Amostra selecionada: {effective_sample} de {total_rows} linhas "
            f"({pct_sent:.2f}% enviado, {pct_saved:.2f}% economizado)"
        )

    # Converte colunas para string para classificacao uniforme
    df_str = df_sample.astype(str)

    # --- Deteccao de colunas sensiveis ---
    col_types = {}  # type: Dict[str, Optional[str]]
    date_columns = []  # type: List[str]

    for col in df_sample.columns:
        kind = detect_sensitivity(col)
        source = "header"

        # False = explicitamente nao-sensivel (whitelist) - nao roda heuristica
        # None = sem match por header - tenta heuristica de conteudo
        if kind is False:
            kind = None
        elif kind is None:
            # Verificar se e coluna de data (nativa datetime64 ou parseavel)
            if _is_date_column(df_sample[col]):
                date_columns.append(col)
                kind = "date"
                source = "conteudo"
            else:
                col_type = detect_column_type(df_str[col])
                source = "conteudo"
                if col_type == "id_number":
                    kind = "id_number"
                elif col_type == "amount":
                    kind = "amount"
                elif col_type == "name":
                    kind = "name"
                elif col_type == "financial_text":
                    kind = "amount"
                # "enum" e "mixed" ficam como None (nao-sensivel)

        col_types[col] = kind
        if kind:
            log.info(f"  Coluna sensivel ({source}): '{col}' -> tipo '{kind}'")
        else:
            log.info(f"  Coluna nao-sensivel: '{col}'")

    # --- Renomeacao de colunas ---
    col_rename_map = {}  # type: Dict[str, str]
    for i, col in enumerate(df_sample.columns):
        col_rename_map[col] = _col_code(i)

    # Converter tudo para object para permitir substituicoes mistas de tipo
    df_anon = df_sample.copy()
    for col in df_anon.columns:
        df_anon[col] = df_anon[col].astype(object)

    df_anon = df_anon.rename(columns=col_rename_map)

    # --- Anonimizacao dos valores sensiveis ---
    for original_col, kind in col_types.items():
        if kind is None:
            continue
        new_col = col_rename_map[original_col]

        if kind == "date":
            log.info(f"  Anonimizando coluna de data: {new_col}")
            df_anon[new_col] = df_sample[original_col].apply(_anonymize_date)
        else:
            log.info(f"  Anonimizando coluna: {new_col} (tipo={kind})")
            df_anon[new_col] = df_sample[original_col].apply(
                lambda v, k=kind: _anonymize_cell(v, k)
            )

    # --- C-02: Aplica text_engine em colunas de texto livre nao-sensiveis ---
    text_eng = TextAnonymizer()
    freetext_cols = []  # type: List[str]

    for original_col, kind in col_types.items():
        if kind is not None:
            continue  # ja anonimizada
        new_col = col_rename_map[original_col]
        if _is_freetext_column(df_sample[original_col]):
            freetext_cols.append(original_col)
            log.info(
                f"  Texto livre detectado em '{original_col}' -> "
                f"aplicando text_engine"
            )
            df_anon[new_col] = df_sample[original_col].apply(
                lambda v: text_eng.anonymize(str(v))
                if pd.notna(v) and str(v).strip()
                else v
            )

    if freetext_cols:
        log.info(
            f"  text_engine aplicado em {len(freetext_cols)} coluna(s) "
            f"de texto livre"
        )

    # --- Validacao de seguranca (C-01: BLOQUEIA em caso de vazamento) ---
    anon_filename = f"anon_{stem}_{timestamp}.parquet"
    anon_path = ANONYMIZED_DIR / anon_filename

    _validate_no_leakage(df_sample, df_anon, col_types, col_rename_map, anon_path)

    # --- Salvar arquivo anonimizado ---
    try:
        df_anon.to_parquet(anon_path, index=False, engine="pyarrow")
        log.info(f"Arquivo anonimizado salvo (Parquet): {anon_path}")
    except Exception as e:
        log.warning(
            f"Falha ao salvar como Parquet ({e}). "
            f"Tentando fallback para CSV..."
        )
        anon_filename = f"anon_{stem}_{timestamp}.csv"
        anon_path = ANONYMIZED_DIR / anon_filename
        df_anon.to_csv(anon_path, index=False)
        log.info(f"Arquivo anonimizado salvo (CSV fallback): {anon_path}")

    # --- Salvar mapa de correspondencia ---
    sensitive_count = sum(1 for k in col_types.values() if k is not None)

    # Contagem de entidades por tipo
    entity_counts = {}  # type: Dict[str, int]
    for col, kind in col_types.items():
        if kind is not None:
            entity_counts[kind] = entity_counts.get(kind, 0) + 1

    map_data = {
        "timestamp": datetime.now().isoformat(),
        "tipo": "planilha",
        "formato_original": ".parquet",
        "arquivo_original": str(input_path),
        "arquivo_anonimizado": str(anon_path),
        "total_linhas_original": total_rows,
        "total_linhas_amostra": len(df_anon),
        "pct_enviado": round(pct_sent, 2),
        "pct_economizado": round(pct_saved, 2),
        "amostragem": "manual" if sample_size is not None else "automatica",
        "entidades": entity_counts,
        "estatisticas": {
            "total_colunas": total_cols,
            "colunas_sensiveis": sensitive_count,
            "colunas_texto_livre": len(freetext_cols),
            "total_entidades": sensitive_count,
        },
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

    log.info(f"Mapa de correspondencia salvo: {map_path}")

    # --- Resumo ---
    log.info(
        f"Anonimizacao concluida: {sensitive_count}/{total_cols} colunas "
        f"sensiveis + {len(freetext_cols)} texto livre | "
        f"Tamanho real: {total_rows} | Amostra: {len(df_anon)} | "
        f"Enviado: {pct_sent:.2f}% | Economizado: {pct_saved:.2f}%"
    )

    return anon_path, map_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PSA Guardiao - Anonimizador de arquivos Parquet"
    )
    parser.add_argument("arquivo", help="Caminho para o arquivo Parquet a anonimizar")
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help=(
            "Numero de linhas na amostra "
            "(omita para amostragem inteligente automatica)"
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.arquivo)
    if not input_path.exists():
        log.error(f"Arquivo nao encontrado: {input_path}")
        sys.exit(1)

    if input_path.suffix.lower() != ".parquet":
        log.error(f"Arquivo deve ser Parquet. Recebido: {input_path.suffix}")
        sys.exit(1)

    try:
        anon_path, map_path = anonymize_parquet(
            input_path, sample_size=args.sample,
        )
    except LeakageError:
        log.error("Operacao abortada por vazamento de dados.")
        sys.exit(2)

    print("\n" + "=" * 60)
    print("PSA GUARDIAO - ANONIMIZACAO CONCLUIDA")
    print("=" * 60)
    print(f"  Arquivo anonimizado    : {anon_path}")
    print(f"  Mapa de correspondencia: {map_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
