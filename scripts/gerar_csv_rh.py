"""
Gera CSV realista de exportação de sistema de RH com 50 funcionários.
Dados 100% fictícios, estrutura real.
"""
import csv
import random
from pathlib import Path
from faker import Faker

fake = Faker("pt_BR")
random.seed(42)
Faker.seed(42)

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "real" / "funcionarios_rh.csv"

DEPARTAMENTOS = [
    "Financeiro", "Recursos Humanos", "Tecnologia da Informação",
    "Comercial", "Jurídico", "Marketing", "Operações", "Logística",
    "Controladoria", "Compliance"
]

CARGOS = {
    "Financeiro": ["Analista Financeiro", "Coordenador Financeiro", "Gerente Financeiro", "Assistente Financeiro"],
    "Recursos Humanos": ["Analista de RH", "Coordenador de RH", "Gerente de RH", "Assistente de RH"],
    "Tecnologia da Informação": ["Desenvolvedor Sênior", "Analista de Sistemas", "Gerente de TI", "DBA", "Arquiteto de Software"],
    "Comercial": ["Executivo de Vendas", "Coordenador Comercial", "Gerente Comercial", "Assistente Comercial"],
    "Jurídico": ["Advogado Pleno", "Advogado Sênior", "Gerente Jurídico", "Paralegal"],
    "Marketing": ["Analista de Marketing", "Coordenador de Marketing", "Gerente de Marketing", "Designer"],
    "Operações": ["Analista de Operações", "Coordenador de Operações", "Gerente de Operações", "Assistente de Operações"],
    "Logística": ["Analista de Logística", "Coordenador de Logística", "Gerente de Logística", "Auxiliar de Logística"],
    "Controladoria": ["Controller", "Analista Contábil", "Coordenador de Controladoria", "Assistente Contábil"],
    "Compliance": ["Analista de Compliance", "Coordenador de Compliance", "Gerente de Compliance", "Auditor Interno"],
}

FAIXAS_SALARIAIS = {
    "Assistente": (2800, 4200), "Auxiliar": (2500, 3800),
    "Analista": (5500, 9500), "Designer": (5000, 8500),
    "Paralegal": (4000, 6500), "Desenvolvedor": (9000, 16000),
    "DBA": (10000, 15000), "Arquiteto": (14000, 22000),
    "Advogado": (8000, 15000), "Executivo": (6000, 12000),
    "Coordenador": (8500, 14000), "Controller": (12000, 18000),
    "Auditor": (7000, 12000), "Gerente": (14000, 25000),
}

BANCOS = [
    ("Itaú", "341"), ("Bradesco", "237"), ("Banco do Brasil", "001"),
    ("Santander", "033"), ("Caixa", "104"), ("Nubank", "260"),
    ("Inter", "077"), ("BTG Pactual", "208"),
]

PLANOS = ["Bradesco Saúde", "SulAmérica", "Amil", "Unimed", "Notre Dame Intermédica"]

GESTORES = [fake.name() for _ in range(8)]

def faixa_salarial(cargo):
    for key, (lo, hi) in FAIXAS_SALARIAIS.items():
        if key in cargo:
            return round(random.uniform(lo, hi), 2)
    return round(random.uniform(5000, 12000), 2)

def gerar_cpf():
    n = [random.randint(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(n) + 1 - i) * v for i, v in enumerate(n))
        d = 11 - (s % 11)
        n.append(d if d < 10 else 0)
    return f"{n[0]}{n[1]}{n[2]}.{n[3]}{n[4]}{n[5]}.{n[6]}{n[7]}{n[8]}-{n[9]}{n[10]}"

def gerar_rg():
    return f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(0,9)}"

rows = []
for i in range(50):
    dept = random.choice(DEPARTAMENTOS)
    cargo = random.choice(CARGOS[dept])
    nome = fake.name()
    salario = faixa_salarial(cargo)
    banco_nome, banco_cod = random.choice(BANCOS)
    agencia = f"{random.randint(1, 9999):04d}"
    conta = f"{random.randint(10000, 999999):06d}-{random.randint(0,9)}"
    pix_tipo = random.choice(["cpf", "email", "telefone"])
    cpf = gerar_cpf()

    if pix_tipo == "cpf":
        chave_pix = cpf
    elif pix_tipo == "email":
        chave_pix = nome.lower().replace(" ", ".") + "@email.com"
    else:
        ddd = random.choice(["11", "21", "31", "41", "51", "61", "71", "81"])
        chave_pix = f"({ddd}) 9{random.randint(1000,9999):04d}-{random.randint(1000,9999):04d}"

    email_corp = nome.split()[0].lower() + "." + nome.split()[-1].lower() + "@grupoatlas.com.br"

    rows.append({
        "nome": nome,
        "cpf": cpf,
        "rg": gerar_rg(),
        "data_nascimento": fake.date_of_birth(minimum_age=22, maximum_age=62).strftime("%d/%m/%Y"),
        "cargo": cargo,
        "departamento": dept,
        "salario": f"{salario:.2f}".replace(".", ","),
        "data_admissao": fake.date_between(start_date="-15y", end_date="-30d").strftime("%d/%m/%Y"),
        "email_corporativo": email_corp,
        "telefone": fake.cellphone_number(),
        "endereco": fake.street_address() + ", " + fake.city() + "/" + fake.state_abbr(),
        "cep": fake.postcode(),
        "banco": f"{banco_nome} ({banco_cod})",
        "agencia": agencia,
        "conta": conta,
        "chave_pix": chave_pix,
        "plano_saude": random.choice(PLANOS),
        "numero_carteirinha": f"{random.randint(100000000, 999999999):09d}",
        "gestor_direto": random.choice(GESTORES),
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV gerado: {OUTPUT}")
print(f"Linhas: {len(rows)} | Colunas: {len(rows[0])}")
print(f"Tamanho: {OUTPUT.stat().st_size:,} bytes")
