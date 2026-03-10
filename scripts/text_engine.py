"""
PSA - Privacy Shield Agent
Módulo: text_engine.py

Motor de anonimização de texto livre.
Usado por anonymize_document.py, anonymize_pdf.py e anonymize_presentation.py.

Detecta e substitui via regex:
  - CPF, CNPJ, RG, PIS/PASEP/NIS, CTPS, CNH
  - Emails
  - Telefones brasileiros
  - Valores monetários (R$)
  - Datas (BR e ISO)
  - CEPs
  - Endereços (rua, avenida, etc.)
  - Processos judiciais
  - Nomes de pessoas (inclusive ALL-CAPS e com honoríficos)
  - Nomes de empresas

NÃO acessa internet. Tudo roda localmente com Faker pt_BR.
"""

import os
import re
import hashlib
from typing import Dict, Tuple

from faker import Faker

fake = Faker("pt_BR")
# C-03 / H-01: Seed aleatório baseado em entropia do SO (não determinístico)
Faker.seed(int.from_bytes(os.urandom(8), "big"))

# ---------------------------------------------------------------------------
# Padrões regex
# ---------------------------------------------------------------------------

# CPF: 000.000.000-00 ou 00000000000
_CPF = re.compile(
    r'\b\d{3}\.?\d{3}\.?\d{3}[-–]?\d{2}\b'
)

# CNPJ: 00.000.000/0000-00 ou variações
_CNPJ = re.compile(
    r'\b\d{2}\.?\d{3}\.?\d{3}[/\\]?\d{4}[-–]?\d{2}\b'
)

# RG: 00.000.000-0 ou variações (7-10 dígitos com separadores)
_RG = re.compile(
    r'\b\d{1,2}\.?\d{3}\.?\d{3}[-–]?[\dXx]\b'
)

# PIS/PASEP/NIS/NIT: 000.00000.00-0 (11 dígitos)
_PIS = re.compile(
    r'\b\d{3}\.?\d{5}\.?\d{2}[-–]?\d{1}\b'
)

# CTPS: 0000000 0000-UF (7 dígitos série + 4 dígitos número)
_CTPS = re.compile(
    r'\b\d{7}\s*/?\s*\d{4}(?:\s*[-–]\s*[A-Z]{2})?\b'
)

# CNH: 00000000000 (11 dígitos)
_CNH = re.compile(
    r'\b\d{11}\b'
)

# Email
_EMAIL = re.compile(
    r'\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b'
)

# Telefone brasileiro: (11) 99999-9999 | +55 11 9999-9999 | 0800 xxx xxxx
_PHONE = re.compile(
    r'(?:\+55\s?)?'
    r'(?:\(?\d{2}\)?\s?)'
    r'(?:9\s?)?\d{4}[-\s]?\d{4}'
    r'|0800\s?\d{3}\s?\d{4}'
)

# Valor monetário: R$ 1.234,56 | 1234,56 reais | 10 mil reais
_MONETARY = re.compile(
    r'R\$\s*[\d.,]+(?:\s*(?:mil(?:hões?)?|bilhões?|trilhões?))?'
    r'|\b[\d]{1,3}(?:\.\d{3})*(?:,\d{2})?\s*(?:reais?|BRL)\b',
    re.IGNORECASE
)

# Data BR: 01/01/2024 | 01-01-2024 | 01.01.2024 | 1º de janeiro de 2024
_DATE_BR = re.compile(
    r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b'
    r'|\b\d{1,2}\s+de\s+[a-záéíóúàãõ]+\s+de\s+\d{4}\b'
    r'|\b\d{1,2}º?\s+de\s+[a-záéíóúàãõ]+\s+de\s+\d{4}\b',
    re.IGNORECASE
)

# Data ISO: 2024-01-31 | 2024-01-31T10:30:00
_DATE_ISO = re.compile(
    r'\b\d{4}[-/]\d{2}[-/]\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?\b'
)

# CEP: 01310-100 ou 01310100
_CEP = re.compile(
    r'\b\d{5}-?\d{3}\b'
)

# Número de processo judicial: 0000000-00.0000.0.0000.0000
_PROCESSO = re.compile(
    r'\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b'
)

# Endereços: Rua/Av./Alameda/Travessa/etc. seguido de texto e número
_ADDRESS = re.compile(
    r'\b(?:Rua|R\.|Avenida|Av\.|Alameda|Al\.|Travessa|Tv\.|Rodovia|Rod\.|'
    r'Praça|Pç\.|Estrada|Est\.|Largo|Viela|Beco|Servidão)'
    r'\s+[A-Za-záéíóúàãõâêôüçÁÉÍÓÚÀÃÕÂÊÔÜÇ\s]+(?:,?\s*(?:n[.ºo]?\s*)?\d+)?',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Nomes: suporta Mixed Case E ALL-CAPS, com honoríficos e sufixos
# ---------------------------------------------------------------------------

# Honoríficos que precedem nomes
_HONORIFICS = r'(?:Dr\.?a?|Sr\.?a?|Prof\.?a?|Des\.?|Min\.?|Adv\.?|Eng\.?|Arq\.?|Cel\.?|Cap\.?|Sgt\.?|Ten\.?|Maj\.?|Gen\.?|Dep\.?|Sen\.?|Gov\.?|Pres\.?)'

# Sufixos familiares
_SUFFIXES = r'(?:\s+(?:Filho|Filha|Junior|Júnior|Jr\.?|Neto|Neta|Sobrinho|Sobrinha|Segundo|Terceiro|II|III|IV))'

# Partículas de ligação
_PARTICLES = r'(?:da|de|do|das|dos|e|van|von|di|del|Del|Da|De|Do|Das|Dos|DE|DA|DO|DAS|DOS|E)'

# Nome em Mixed Case: "João da Silva Neto"
_NAME_MIXED = re.compile(
    r'\b'
    + _HONORIFICS + r'?\s*'
    r'[A-ZÁÉÍÓÚÀÃÕÂÊÔÜÇ][a-záéíóúàãõâêôüç]+'
    r'(?:\s+' + _PARTICLES + r')*'
    r'(?:\s+[A-ZÁÉÍÓÚÀÃÕÂÊÔÜÇ][a-záéíóúàãõâêôüç]+){1,5}'
    + _SUFFIXES + r'?'
    r'\b'
)

# Nome em ALL-CAPS: "JOÃO DA SILVA NETO" (mínimo 2 palavras, cada com 2+ letras)
_NAME_UPPER = re.compile(
    r'\b'
    + _HONORIFICS.upper() + r'?\s*'
    r'[A-ZÁÉÍÓÚÀÃÕÂÊÔÜÇ]{2,}'
    r'(?:\s+(?:DA|DE|DO|DAS|DOS|E|VAN|VON|DI|DEL))*'
    r'(?:\s+[A-ZÁÉÍÓÚÀÃÕÂÊÔÜÇ]{2,}){1,5}'
    + _SUFFIXES.upper().replace(r'\s+', r'\s+') + r'?'
    r'\b'
)

# Palavras que NÃO são nomes (evita substituir cidades, títulos, termos jurídicos etc.)
_NOT_A_NAME = {
    # meses
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    # estados / regiões
    "são paulo", "rio de janeiro", "minas gerais", "espírito santo",
    "mato grosso", "mato grosso do sul", "rio grande do sul",
    "rio grande do norte", "santa catarina", "distrito federal",
    "pará", "paraná", "paraíba", "pernambuco", "piauí",
    "maranhão", "goiás", "bahia", "ceará", "amazonas",
    "tocantins", "rondônia", "roraima", "amapá", "acre",
    "sergipe", "alagoas",
    # siglas de estados (ALL-CAPS)
    "ac", "al", "ap", "am", "ba", "ce", "df", "es", "go",
    "ma", "mt", "ms", "mg", "pa", "pb", "pr", "pe", "pi",
    "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to",
    # termos jurídicos e comuns
    "excelência", "vossa excelência", "vossas excelências",
    "meritíssimo", "douto", "ilustre", "nobre",
    "código civil", "código penal", "lei federal", "decreto lei",
    "supremo tribunal", "superior tribunal", "tribunal de justiça",
    "tribunal de contas", "ministério público", "poder executivo",
    "poder legislativo", "poder judiciário", "governo federal",
    "governo estadual", "governo distrital", "câmara legislativa",
    "senado federal", "câmara dos deputados",
    # instituições governamentais comuns
    "banco central", "receita federal", "caixa econômica",
    "polícia federal", "polícia civil", "polícia militar",
    "corpo de bombeiros", "forças armadas",
    "secretaria de estado", "secretaria de saúde",
    "secretaria de educação", "secretaria de fazenda",
    # termos financeiros / administrativos comuns ALL-CAPS
    "remuneração básica", "bruto", "líquido", "desconto",
    "gratificação", "adicional", "abono", "auxílio",
    "total geral", "valor total", "subtotal",
    "ativo permanente", "ativo", "inativo",
}

# Versão ALL-CAPS de _NOT_A_NAME para comparação rápida
_NOT_A_NAME_UPPER = {n.upper() for n in _NOT_A_NAME}

# ---------------------------------------------------------------------------
# Geradores sintéticos
# ---------------------------------------------------------------------------

def _fake_cpf() -> str:
    digits = [fake.random_int(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(digits) + 1 - i) * v for i, v in enumerate(digits))
        d = (s * 10 % 11) % 10
        digits.append(d)
    return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*digits)


def _fake_cnpj() -> str:
    def calc(ds, weights):
        s = sum(d * w for d, w in zip(ds, weights))
        r = s % 11
        return 0 if r < 2 else 11 - r
    base = [fake.random_int(0, 9) for _ in range(8)] + [0, 0, 0, 1]
    d1 = calc(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = calc(base + [d1], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    n = base + [d1, d2]
    return "{}{}.{}{}{}.{}{}{}/{}{}{}{}-{}{}".format(*n)


def _anonymize_monetary(value: str) -> str:
    """Mantém ordem de grandeza, troca valor exato."""
    nums = re.findall(r'[\d.,]+', value)
    if not nums:
        return value
    try:
        num_str = nums[0].replace(".", "").replace(",", ".")
        num = float(num_str)
        if num == 0:
            return value
        variation = fake.random.uniform(0.85, 1.15)
        new_val = num * variation
        # Formata como moeda brasileira
        new_str = f"{new_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if "R$" in value:
            return f"R$ {new_str}"
        if re.search(r'reais?', value, re.IGNORECASE):
            return f"{new_str} reais"
        return new_str
    except (ValueError, IndexError):
        return value


def _anonymize_date(value: str) -> str:
    """Substitui data por data sintética próxima."""
    new_date = fake.date_between(start_date="-5y", end_date="today")
    # Data ISO
    if re.match(r'\d{4}[-/]\d{2}[-/]\d{2}', value):
        fmt = "%Y-%m-%d"
        if "T" in value or " " in value.strip():
            fmt += "T%H:%M:%S"
            return new_date.strftime("%Y-%m-%d") + "T" + fake.time()
        return new_date.strftime(fmt)
    # Data BR
    if "/" in value:
        return new_date.strftime("%d/%m/%Y")
    if "-" in value and len(value) <= 10:
        return new_date.strftime("%d-%m-%Y")
    if "." in value and len(value) <= 10:
        return new_date.strftime("%d.%m.%Y")
    # Data por extenso
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    return f"{new_date.day} de {meses[new_date.month-1]} de {new_date.year}"


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------

class TextAnonymizer:
    """
    Anonimiza texto livre.

    Mantém cache para consistência: mesma entidade original → mesmo substituto.
    Registra todas as substituições no entity_map para o arquivo de mapa.
    """

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self.entity_map: Dict[str, str] = {}
        self._counters = {
            "pessoa": 0,
            "empresa": 0,
        }

    def _cached_replace(self, original: str, generator_fn) -> str:
        # SHA-256 em vez de MD5 (M-07: hash criptográfico)
        key = hashlib.sha256(original.lower().strip().encode()).hexdigest()
        if key not in self._cache:
            replacement = generator_fn()
            self._cache[key] = replacement
            self.entity_map[replacement] = original
        return self._cache[key]

    def _next_token(self, kind: str) -> str:
        self._counters[kind] += 1
        return f"[{kind.upper()}_{self._counters[kind]}]"

    def _replace_cpf(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), _fake_cpf)

    def _replace_cnpj(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), _fake_cnpj)

    def _replace_rg(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), lambda: str(fake.random_number(digits=9)))

    def _replace_pis(self, m: re.Match) -> str:
        return self._cached_replace(
            m.group(),
            lambda: "{}.{}.{}-{}".format(
                fake.random_number(digits=3),
                fake.random_number(digits=5),
                fake.random_number(digits=2),
                fake.random_int(0, 9),
            )
        )

    def _replace_ctps(self, m: re.Match) -> str:
        return self._cached_replace(
            m.group(),
            lambda: f"{fake.random_number(digits=7)}/{fake.random_number(digits=4)}"
        )

    def _replace_email(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), fake.email)

    def _replace_phone(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), fake.phone_number)

    def _replace_monetary(self, m: re.Match) -> str:
        return _anonymize_monetary(m.group())

    def _replace_date(self, m: re.Match) -> str:
        return _anonymize_date(m.group())

    def _replace_cep(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), fake.postcode)

    def _replace_processo(self, m: re.Match) -> str:
        def gen():
            r = fake.random_number
            return f"{r(7)}-{r(2):02d}.{r(4):04d}.{fake.random_int(1,9)}.{fake.random_int(10,99)}.{r(4):04d}"
        return self._cached_replace(m.group(), gen)

    def _replace_address(self, m: re.Match) -> str:
        return self._cached_replace(m.group(), fake.address)

    def _replace_name(self, m: re.Match) -> str:
        txt = m.group().strip()
        # Ignora se for termo conhecido que não é nome de pessoa
        txt_lower = txt.lower()
        if txt_lower in _NOT_A_NAME:
            return txt
        if txt.upper() in _NOT_A_NAME_UPPER and txt.isupper():
            return txt
        # Ignora strings muito curtas (1 palavra só)
        words = [w for w in txt.split() if len(w) > 1]
        if len(words) < 2:
            return txt
        # Ignora se todas as palavras têm 2 letras ou menos (siglas)
        if all(len(w) <= 2 for w in words):
            return txt

        key = hashlib.sha256(txt_lower.encode()).hexdigest()
        if key not in self._cache:
            # Heurística: se termina com Ltda, S.A., ME etc. → empresa
            if re.search(r'\b(?:ltda|s\.?a\.?|eireli|me|epp|ss|sc)\b', txt, re.IGNORECASE):
                token = self._next_token("empresa")
            else:
                token = self._next_token("pessoa")
            self._cache[key] = token
            self.entity_map[token] = txt
        return self._cache[key]

    def anonymize(self, text: str) -> str:
        """
        Aplica todas as substituições ao texto, na ordem correta.
        Ordem importa: estruturados primeiro (CPF, CNPJ, etc.) para evitar
        que o padrão de nomes capture partes de CPFs/CNPJs.
        """
        # 1. Processos judiciais (específico, antes de datas e números genéricos)
        text = _PROCESSO.sub(self._replace_processo, text)
        # 2. CNPJ antes de CPF (CNPJ tem mais dígitos, evitar match parcial)
        text = _CNPJ.sub(self._replace_cnpj, text)
        # 3. CPF
        text = _CPF.sub(self._replace_cpf, text)
        # 4. PIS/PASEP/NIS
        text = _PIS.sub(self._replace_pis, text)
        # 5. CTPS
        text = _CTPS.sub(self._replace_ctps, text)
        # 6. Email
        text = _EMAIL.sub(self._replace_email, text)
        # 7. CEP (antes de telefone para evitar conflitos)
        text = _CEP.sub(self._replace_cep, text)
        # 8. Telefone
        text = _PHONE.sub(self._replace_phone, text)
        # 9. Valores monetários
        text = _MONETARY.sub(self._replace_monetary, text)
        # 10. Datas ISO (antes de BR para evitar conflitos)
        text = _DATE_ISO.sub(self._replace_date, text)
        # 11. Datas BR
        text = _DATE_BR.sub(self._replace_date, text)
        # 12. Endereços (antes de nomes para evitar que nome capture rua)
        text = _ADDRESS.sub(self._replace_address, text)
        # 13. Nomes ALL-CAPS (antes de mixed para evitar conflitos)
        text = _NAME_UPPER.sub(self._replace_name, text)
        # 14. Nomes Mixed Case (por último, heurística)
        text = _NAME_MIXED.sub(self._replace_name, text)
        return text

    def reset(self):
        """Reseta contadores mas mantém cache (para consistência entre documentos)."""
        self._counters = {"pessoa": 0, "empresa": 0}


def anonymize_text(text: str, engine: "TextAnonymizer" = None) -> Tuple[str, Dict[str, str]]:
    """
    Conveniência: anonimiza texto e retorna (texto_anonimizado, entity_map).
    Se engine for fornecido, reutiliza o cache existente.
    """
    if engine is None:
        engine = TextAnonymizer()
    anon = engine.anonymize(text)
    return anon, engine.entity_map
