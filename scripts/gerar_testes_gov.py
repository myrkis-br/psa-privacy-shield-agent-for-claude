"""
Gera 6 arquivos de teste robustos com dados públicos reais
da Câmara dos Deputados (API aberta, dados públicos por lei).

Formatos: HTML, YAML, SQL, LOG, VCF, PARQUET
"""
import json
import os
import random
from pathlib import Path
from datetime import datetime, timedelta

# Credenciais fictícias para dados de teste — carregadas via env var
# para não expor padrões realistas no código-fonte.
_TEST_CREDS = {
    "db_password": os.environ.get("PSA_TEST_DB_PASS", "FAKE_DB_PASS_PLACEHOLDER"),
    "redis_password": os.environ.get("PSA_TEST_REDIS_PASS", "FAKE_REDIS_PASS_PLACEHOLDER"),
    "jwt_secret": os.environ.get("PSA_TEST_JWT_SECRET", "FAKE_JWT_SECRET_PLACEHOLDER"),
    "admin_api_key": os.environ.get("PSA_TEST_ADMIN_KEY", "FAKE_ADMIN_KEY_PLACEHOLDER"),
    "datadog_api_key": os.environ.get("PSA_TEST_DD_KEY", "FAKE_DD_KEY_PLACEHOLDER"),
    "smtp_password": os.environ.get("PSA_TEST_SMTP_PASS", "FAKE_SMTP_PASS_PLACEHOLDER"),
    "webhook_secret": os.environ.get("PSA_TEST_WH_SECRET", "FAKE_WH_SECRET_PLACEHOLDER"),
    "aws_access_key": os.environ.get("PSA_TEST_AWS_KEY", "FAKE_AWS_KEY_PLACEHOLDER"),
    "aws_secret_key": os.environ.get("PSA_TEST_AWS_SECRET", "FAKE_AWS_SECRET_PLACEHOLDER"),
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "real"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ─── Dados reais da API da Câmara dos Deputados ───────────────────────────
DEPUTADOS_DETALHADOS = [
    {
        "nome_civil": "Acácio da Silva Favacho Neto",
        "nome_eleitoral": "Acácio Favacho",
        "cpf": "742.870.282-87",
        "nascimento": "1983-09-28",
        "naturalidade": "Macapá/AP",
        "escolaridade": "Superior",
        "partido": "MDB",
        "uf": "AP",
        "email": "dep.acaciofavacho@camara.leg.br",
        "telefone": "(61) 3215-5414",
        "gabinete": "414",
        "predio": "4",
    },
    {
        "nome_civil": "Adail José Figueiredo Pinheiro",
        "nome_eleitoral": "Adail Filho",
        "cpf": "772.677.962-49",
        "nascimento": "1992-02-16",
        "naturalidade": "Manaus/AM",
        "escolaridade": "Superior Incompleto",
        "partido": "REPUBLICANOS",
        "uf": "AM",
        "email": "dep.adailfilho@camara.leg.br",
        "telefone": "(61) 3215-5531",
        "gabinete": "531",
        "predio": "4",
    },
    {
        "nome_civil": "Adriana Miguel Ventura",
        "nome_eleitoral": "Adriana Ventura",
        "cpf": "125.198.518-13",
        "nascimento": "1969-03-06",
        "naturalidade": "São Paulo/SP",
        "escolaridade": "Doutorado",
        "partido": "NOVO",
        "uf": "SP",
        "email": "dep.adrianaventura@camara.leg.br",
        "telefone": "(61) 3215-5802",
        "gabinete": "802",
        "predio": "4",
    },
    {
        "nome_civil": "Aécio Neves da Cunha",
        "nome_eleitoral": "Aécio Neves",
        "cpf": "667.289.837-91",
        "nascimento": "1960-03-10",
        "naturalidade": "Belo Horizonte/MG",
        "escolaridade": "Superior",
        "partido": "PSDB",
        "uf": "MG",
        "email": "dep.aecioneves@camara.leg.br",
        "telefone": "(61) 3215-5964",
        "gabinete": "20",
        "predio": "X",
    },
    {
        "nome_civil": "Aguinaldo Velloso Borges Ribeiro",
        "nome_eleitoral": "Aguinaldo Ribeiro",
        "cpf": "519.211.464-00",
        "nascimento": "1969-02-13",
        "naturalidade": "Campina Grande/PB",
        "escolaridade": "Pós-graduação",
        "partido": "PP",
        "uf": "PB",
        "email": "dep.aguinaldoribeiro@camara.leg.br",
        "telefone": "(61) 3215-5735",
        "gabinete": "735",
        "predio": "4",
    },
]

DEPUTADOS_LISTA = [
    ("Acácio Favacho", "MDB", "AP", "dep.acaciofavacho@camara.leg.br"),
    ("Adail Filho", "REPUBLICANOS", "AM", "dep.adailfilho@camara.leg.br"),
    ("Adilson Barroso", "PL", "SP", "dep.adilsonbarroso@camara.leg.br"),
    ("Adolfo Viana", "PSDB", "BA", "dep.adolfoviana@camara.leg.br"),
    ("Adriana Ventura", "NOVO", "SP", "dep.adrianaventura@camara.leg.br"),
    ("Adriano do Baldy", "PP", "GO", "dep.adrianodobaldy@camara.leg.br"),
    ("Aécio Neves", "PSDB", "MG", "dep.aecioneves@camara.leg.br"),
    ("Afonso Hamm", "PP", "RS", "dep.afonsohamm@camara.leg.br"),
    ("Afonso Motta", "PDT", "RS", "dep.afonsomotta@camara.leg.br"),
    ("Aguinaldo Ribeiro", "PP", "PB", "dep.aguinaldoribeiro@camara.leg.br"),
    ("Airton Faleiro", "PT", "PA", "dep.airtonfaleiro@camara.leg.br"),
    ("AJ Albuquerque", "PP", "CE", "dep.ajalbuquerque@camara.leg.br"),
    ("Alberto Fraga", "PL", "DF", "dep.albertofraga@camara.leg.br"),
    ("Albuquerque", "REPUBLICANOS", "RR", "dep.albuquerque@camara.leg.br"),
    ("Alceu Moreira", "MDB", "RS", "dep.alceumoreira@camara.leg.br"),
    ("Alencar Santana", "PT", "SP", "dep.alencarsantana@camara.leg.br"),
    ("Alex Manente", "CIDADANIA", "SP", "dep.alexmanente@camara.leg.br"),
    ("Alex Santana", "REPUBLICANOS", "BA", "dep.alexsantana@camara.leg.br"),
    ("Alexandre Guimarães", "MDB", "TO", "dep.alexandreguimaraes@camara.leg.br"),
    ("Alexandre Lindenmeyer", "PT", "RS", "dep.alexandrelindenmeyer@camara.leg.br"),
    ("Alfredinho", "PT", "SP", "dep.alfredinho@camara.leg.br"),
    ("Alfredo Gaspar", "UNIÃO", "AL", "dep.alfredogaspar@camara.leg.br"),
    ("Alice Portugal", "PCdoB", "BA", "dep.aliceportugal@camara.leg.br"),
    ("Aliel Machado", "PV", "PR", "dep.alielmachado@camara.leg.br"),
    ("Allan Garcês", "PP", "MA", "dep.allangarces@camara.leg.br"),
    ("Altineu Côrtes", "PL", "RJ", "dep.altineucortes@camara.leg.br"),
    ("Aluisio Mendes", "REPUBLICANOS", "MA", "dep.aluisiomendes@camara.leg.br"),
    ("Amanda Gentil", "PP", "MA", "dep.amandagentil@camara.leg.br"),
    ("Amaro Neto", "REPUBLICANOS", "ES", "dep.amaroneto@camara.leg.br"),
    ("Amom Mandel", "CIDADANIA", "AM", "dep.amommandel@camara.leg.br"),
    ("Ana Paula Leão", "PP", "MG", "dep.anapaulaleao@camara.leg.br"),
    ("Ana Paula Lima", "PT", "SC", "dep.anapaulalima@camara.leg.br"),
    ("Ana Pimentel", "PT", "MG", "dep.anapimentel@camara.leg.br"),
    ("André Abdon", "PP", "AP", "dep.andreabdon@camara.leg.br"),
    ("André Fernandes", "PL", "CE", "dep.andrefernandes@camara.leg.br"),
    ("André Ferreira", "PL", "PE", "dep.andreferreira@camara.leg.br"),
    ("André Figueiredo", "PDT", "CE", "dep.andrefigueiredo@camara.leg.br"),
    ("André Janones", "AVANTE", "MG", "dep.andrejanones@camara.leg.br"),
    ("Andreia Siqueira", "MDB", "PA", "dep.andreiasiqueira@camara.leg.br"),
    ("Antônia Lúcia", "REPUBLICANOS", "AC", "dep.antonialucia@camara.leg.br"),
    ("Antonio Andrade", "REPUBLICANOS", "TO", "dep.antonioandrade@camara.leg.br"),
    ("Antonio Brito", "PSD", "BA", "dep.antoniobrito@camara.leg.br"),
    ("Antonio Carlos Rodrigues", "PL", "SP", "dep.antoniocarlosrodrigues@camara.leg.br"),
    ("Antônio Doido", "MDB", "PA", "dep.antoniodoido@camara.leg.br"),
    ("Any Ortiz", "CIDADANIA", "RS", "dep.anyortiz@camara.leg.br"),
]

# ─── 1. HTML ──────────────────────────────────────────────────────────────

def gerar_html():
    rows = ""
    for d in DEPUTADOS_DETALHADOS:
        rows += f"""      <tr>
        <td>{d['nome_civil']}</td>
        <td>{d['cpf']}</td>
        <td>{d['nascimento']}</td>
        <td>{d['naturalidade']}</td>
        <td>{d['partido']}/{d['uf']}</td>
        <td>{d['email']}</td>
        <td>{d['telefone']}</td>
        <td>{d['escolaridade']}</td>
        <td>Gabinete {d['gabinete']}, Prédio {d['predio']}</td>
      </tr>
"""
    for nome, partido, uf, email in DEPUTADOS_LISTA[5:]:
        rows += f"""      <tr>
        <td>{nome}</td>
        <td></td>
        <td></td>
        <td></td>
        <td>{partido}/{uf}</td>
        <td>{email}</td>
        <td>(61) 3215-{random.randint(5000,5999)}</td>
        <td></td>
        <td></td>
      </tr>
"""

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Câmara dos Deputados — Relatório de Deputados Federais (57ª Legislatura)</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
    h1 {{ color: #1a5276; border-bottom: 3px solid #2e86c1; padding-bottom: 10px; }}
    h2 {{ color: #2e86c1; }}
    table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    th {{ background: #1a5276; color: white; padding: 12px 8px; text-align: left; font-size: 13px; }}
    td {{ padding: 8px; border-bottom: 1px solid #ddd; font-size: 12px; }}
    tr:hover {{ background: #eaf2f8; }}
    .header {{ background: #1a5276; color: white; padding: 20px; margin: -20px -20px 20px; }}
    .header p {{ margin: 5px 0; }}
    .footer {{ margin-top: 20px; padding: 15px; background: #eee; font-size: 11px; color: #666; }}
    .stats {{ display: flex; gap: 20px; margin: 15px 0; }}
    .stat-box {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; }}
    .stat-box h3 {{ margin: 0 0 5px; color: #1a5276; font-size: 14px; }}
    .stat-box .value {{ font-size: 24px; font-weight: bold; color: #2e86c1; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>Câmara dos Deputados — 57ª Legislatura</h1>
    <p>Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")} | Fonte: API Dados Abertos</p>
    <p>Responsável: Secretaria-Geral da Mesa | Contato: sgm@camara.leg.br | Tel: (61) 3216-1000</p>
  </div>

  <div class="stats">
    <div class="stat-box">
      <h3>Total de Deputados</h3>
      <div class="value">513</div>
    </div>
    <div class="stat-box">
      <h3>Partidos com Representação</h3>
      <div class="value">22</div>
    </div>
    <div class="stat-box">
      <h3>Deputadas Mulheres</h3>
      <div class="value">91</div>
    </div>
  </div>

  <!-- Dados detalhados dos primeiros deputados (ordem alfabética) -->
  <h2>Cadastro Detalhado — Deputados Federais em Exercício</h2>
  <p>Atenção: Este relatório contém dados pessoais protegidos pela LGPD (Lei 13.709/2018).
     CPF e dados de contato são informações públicas conforme Lei de Acesso à Informação (LAI).</p>

  <table>
    <thead>
      <tr>
        <th>Nome Civil Completo</th>
        <th>CPF</th>
        <th>Data de Nascimento</th>
        <th>Naturalidade</th>
        <th>Partido/UF</th>
        <th>Email Institucional</th>
        <th>Telefone Gabinete</th>
        <th>Escolaridade</th>
        <th>Localização</th>
      </tr>
    </thead>
    <tbody>
{rows}    </tbody>
  </table>

  <div class="footer">
    <p>Dados obtidos via API Dados Abertos da Câmara dos Deputados (dadosabertos.camara.leg.br)</p>
    <p>Gerado automaticamente pelo Sistema de Gestão Parlamentar — Câmara dos Deputados</p>
    <p>Este documento é de uso interno. Distribuição não autorizada pode configurar violação da LGPD.</p>
  </div>
</body>
</html>"""

    path = DATA_DIR / "deputados_cadastro.html"
    path.write_text(html, encoding="utf-8")
    print(f"  HTML: {path} ({len(html)} chars, {5 + 40} deputados)")
    return path


# ─── 2. YAML ──────────────────────────────────────────────────────────────

def gerar_yaml():
    yaml_content = """# ============================================================
# Câmara dos Deputados — Configuração do Portal Dados Abertos
# API Gateway — Ambiente de Produção
# Responsável: Coordenação de Sistemas — CENIN
# Contato: cenin@camara.leg.br | Tel: (61) 3216-5100
# ============================================================

application:
  name: "Portal Dados Abertos — Câmara dos Deputados"
  version: "0.4.339"
  environment: production
  base_url: "https://dadosabertos.camara.leg.br/api/v2"
  description: "API REST para consulta de dados legislativos da Câmara dos Deputados"

server:
  host: "10.200.15.42"
  port: 8443
  workers: 8
  ssl_certificate: "/etc/ssl/camara/api-dadosabertos.crt"
  ssl_key: "/etc/ssl/camara/api-dadosabertos.key"

database:
  host: "db-prod-legislativo.camara.gov.br"
  port: 5432
  name: "legislativo_prod"
  username: "api_readonly"
  password: "{db_password}"
  connection_pool: 50
  dsn: "postgresql://api_readonly:{db_password}@db-prod-legislativo.camara.gov.br:5432/legislativo_prod"

redis:
  host: "cache-prod-01.camara.gov.br"
  port: 6379
  password: "{redis_password}"
  database: 0
  ttl_seconds: 300

authentication:
  api_key_header: "chave-api-dados-abertos"
  jwt_secret: "{jwt_secret}"
  token_expiry_hours: 24
  admin_api_key: "{admin_api_key}"

monitoring:
  datadog_api_key: "{datadog_api_key}"
  sentry_dsn: "https://abc123def456@sentry.camara.leg.br/42"
  healthcheck_endpoint: "/api/v2/health"

email_notifications:
  smtp_server: "smtp.camara.leg.br"
  smtp_port: 587
  username: "alertas-api@camara.leg.br"
  password: "{smtp_password}"
  recipients:
    - nome: "Carlos Eduardo Mendes"
      email: "carlos.mendes@camara.leg.br"
      telefone: "(61) 3216-5101"
      cpf: "321.654.987-00"
    - nome: "Maria Fernanda Oliveira"
      email: "maria.oliveira@camara.leg.br"
      telefone: "(61) 3216-5102"
      cpf: "654.987.321-00"
    - nome: "Roberto Silva Neto"
      email: "roberto.neto@camara.leg.br"
      telefone: "(61) 3216-5103"
      cpf: "987.321.654-00"

rate_limiting:
  requests_per_minute: 60
  burst_size: 100
  webhook_url: "https://hooks.camara.leg.br/api-alerts/rate-limit"
  webhook_secret: "{webhook_secret}"

endpoints:
  deputados:
    path: "/deputados"
    cache_ttl: 600
    description: "Listagem e detalhes de deputados federais"
    responsavel: "Secretaria-Geral da Mesa"
    contato: "sgm@camara.leg.br"
  proposicoes:
    path: "/proposicoes"
    cache_ttl: 300
    description: "Proposições legislativas (PL, PEC, MP, etc.)"
  votacoes:
    path: "/votacoes"
    cache_ttl: 120
    description: "Votações em plenário e comissões"
  orgaos:
    path: "/orgaos"
    cache_ttl: 3600
    description: "Comissões, subcomissões e órgãos legislativos"

backup:
  s3_bucket: "s3://camara-backup-legislativo-prod"
  aws_access_key: "{aws_access_key}"
  aws_secret_key: "{aws_secret_key}"
  schedule: "0 2 * * *"
  retention_days: 90

logging:
  level: INFO
  format: "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
  file: "/var/log/camara/api-dados-abertos.log"
  max_size_mb: 500
  rotation: daily
"""
    path = DATA_DIR / "api_config_camara.yaml"
    yaml_content = yaml_content.format(**_TEST_CREDS)
    path.write_text(yaml_content, encoding="utf-8")
    print(f"  YAML: {path} ({len(yaml_content)} chars)")
    return path


# ─── 3. SQL ───────────────────────────────────────────────────────────────

def gerar_sql():
    lines = []
    lines.append("-- ============================================================")
    lines.append("-- Câmara dos Deputados — Dump do Cadastro de Deputados Federais")
    lines.append("-- 57ª Legislatura (2023-2027)")
    lines.append("-- Gerado em: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("-- Responsável: CENIN — Centro de Informática da Câmara")
    lines.append("-- Contato: cenin@camara.leg.br | (61) 3216-5100")
    lines.append("-- DBA: Carlos Eduardo Mendes (carlos.mendes@camara.leg.br)")
    lines.append("-- CPF Responsável: 321.654.987-00")
    lines.append("-- ============================================================")
    lines.append("")
    lines.append("DROP TABLE IF EXISTS deputados;")
    lines.append("")
    lines.append("CREATE TABLE deputados (")
    lines.append("    id SERIAL PRIMARY KEY,")
    lines.append("    nome_civil VARCHAR(200) NOT NULL,")
    lines.append("    nome_eleitoral VARCHAR(100) NOT NULL,")
    lines.append("    cpf CHAR(14) NOT NULL UNIQUE,")
    lines.append("    data_nascimento DATE NOT NULL,")
    lines.append("    naturalidade VARCHAR(100),")
    lines.append("    escolaridade VARCHAR(50),")
    lines.append("    partido VARCHAR(20) NOT NULL,")
    lines.append("    uf CHAR(2) NOT NULL,")
    lines.append("    email VARCHAR(100),")
    lines.append("    telefone VARCHAR(20),")
    lines.append("    gabinete VARCHAR(10),")
    lines.append("    predio VARCHAR(5),")
    lines.append("    situacao VARCHAR(20) DEFAULT 'Exercício',")
    lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    lines.append(");")
    lines.append("")
    lines.append("-- Índices")
    lines.append("CREATE INDEX idx_deputados_partido ON deputados(partido);")
    lines.append("CREATE INDEX idx_deputados_uf ON deputados(uf);")
    lines.append("CREATE UNIQUE INDEX idx_deputados_cpf ON deputados(cpf);")
    lines.append("")
    lines.append("-- ============================================================")
    lines.append("-- Dados detalhados (5 deputados com cadastro completo)")
    lines.append("-- ============================================================")
    lines.append("")
    lines.append("INSERT INTO deputados (nome_civil, nome_eleitoral, cpf, data_nascimento, naturalidade, escolaridade, partido, uf, email, telefone, gabinete, predio) VALUES")

    # Detalhados
    for i, d in enumerate(DEPUTADOS_DETALHADOS):
        comma = "," if i < len(DEPUTADOS_DETALHADOS) - 1 else ";"
        lines.append(
            f"    ('{d['nome_civil']}', '{d['nome_eleitoral']}', '{d['cpf']}', "
            f"'{d['nascimento']}', '{d['naturalidade']}', '{d['escolaridade']}', "
            f"'{d['partido']}', '{d['uf']}', '{d['email']}', '{d['telefone']}', "
            f"'{d['gabinete']}', '{d['predio']}'){comma}"
        )

    lines.append("")
    lines.append("-- ============================================================")
    lines.append("-- Dados resumidos (40 deputados adicionais)")
    lines.append("-- ============================================================")
    lines.append("")
    lines.append("INSERT INTO deputados (nome_civil, nome_eleitoral, cpf, data_nascimento, partido, uf, email, telefone, gabinete, predio) VALUES")

    extras = DEPUTADOS_LISTA[5:]
    for i, (nome, partido, uf, email) in enumerate(extras):
        # Gerar CPF fake para os que nao temos
        cpf = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"
        nasc = f"{random.randint(1955,1995)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        tel = f"(61) 3215-{random.randint(5000,5999)}"
        gab = str(random.randint(100, 999))
        comma = "," if i < len(extras) - 1 else ";"
        lines.append(
            f"    ('{nome}', '{nome}', '{cpf}', '{nasc}', '{partido}', "
            f"'{uf}', '{email}', '{tel}', '{gab}', '4'){comma}"
        )

    lines.append("")
    lines.append("-- Verificação")
    lines.append("SELECT COUNT(*) AS total_deputados FROM deputados;")
    lines.append("SELECT partido, COUNT(*) AS qtd FROM deputados GROUP BY partido ORDER BY qtd DESC;")
    lines.append("")

    content = "\n".join(lines)
    path = DATA_DIR / "dump_deputados_camara.sql"
    path.write_text(content, encoding="utf-8")
    print(f"  SQL: {path} ({len(lines)} linhas, {5+len(extras)} deputados)")
    return path


# ─── 4. LOG ───────────────────────────────────────────────────────────────

def gerar_log():
    ips = [
        "200.192.131.45",   # Câmara rede interna
        "189.28.128.100",   # SERPRO
        "170.66.40.52",     # Senado
        "143.108.240.10",   # USP
        "200.17.202.1",     # UFMG
        "177.8.192.25",     # Cidadão (Brasília)
        "187.45.67.123",    # Cidadão (São Paulo)
        "191.252.100.89",   # Hosting provider
        "104.18.25.100",    # Cloudflare
        "35.190.47.23",     # Google Bot
    ]
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) Safari/605.1.15",
        "python-requests/2.31.0",
        "PostmanRuntime/7.36.1",
        "curl/8.4.0",
        "Googlebot/2.1 (+http://www.google.com/bot.html)",
    ]
    endpoints_log = [
        '/api/v2/deputados?itens=15&ordem=ASC&ordenarPor=nome',
        '/api/v2/deputados/204379',
        '/api/v2/deputados/220714',
        '/api/v2/deputados?siglaUf=SP&siglaPartido=PT',
        '/api/v2/proposicoes?ano=2024&siglaTipo=PL',
        '/api/v2/votacoes?dataInicio=2024-01-01&dataFim=2024-12-31',
        '/api/v2/orgaos?sigla=CCJC',
        '/api/v2/deputados/204528/despesas?ano=2024&mes=6',
        '/api/v2/deputados/74646/orgaos',
        '/api/v2/deputados/160527/discursos?dataInicio=2024-06-01',
    ]
    status_codes = [200, 200, 200, 200, 200, 200, 200, 200, 301, 400, 403, 404, 429, 500]
    api_keys = [
        "chave-api-f8e7d6c5b4a3210",
        "chave-api-9a8b7c6d5e4f3210",
        "chave-api-1234567890abcdef",
        "sess_xK9mP2nQ7rS4tU1v",
        "tok_Bearer_FAKE_TOKEN.abc123.xyz789",
    ]

    lines = []
    base_time = datetime(2025, 3, 10, 8, 0, 0)

    for i in range(200):
        t = base_time + timedelta(seconds=random.randint(0, 86400))
        ip = random.choice(ips)
        endpoint = random.choice(endpoints_log)
        status = random.choice(status_codes)
        ua = random.choice(user_agents)
        size = random.randint(200, 50000)
        resp_time = random.uniform(0.01, 2.5)
        api_key = random.choice(api_keys)

        # Formato de log Apache/NGINX combinado com extras
        line = (
            f'{ip} - - [{t.strftime("%d/%Mar/%Y:%H:%M:%S")} -0300] '
            f'"GET {endpoint} HTTP/1.1" {status} {size} '
            f'"{ua}" api_key={api_key} '
            f'response_time={resp_time:.3f}s'
        )
        lines.append(line)

        # Ocasionalmente adicionar linhas de erro com PII
        if status >= 400 and random.random() > 0.5:
            dep = random.choice(DEPUTADOS_DETALHADOS)
            if status == 403:
                lines.append(
                    f'{t.strftime("%Y-%m-%d %H:%M:%S")} ERROR [auth] '
                    f'Acesso negado para IP {ip} - '
                    f'Tentativa de consulta CPF {dep["cpf"]} '
                    f'(deputado: {dep["nome_civil"]}) - '
                    f'API key inválida: {api_key}'
                )
            elif status == 429:
                lines.append(
                    f'{t.strftime("%Y-%m-%d %H:%M:%S")} WARN [rate-limit] '
                    f'Rate limit excedido para {ip} - '
                    f'User: {dep["email"]} - '
                    f'60 req/min atingido. Bloqueado por 60s.'
                )
            elif status == 500:
                lines.append(
                    f'{t.strftime("%Y-%m-%d %H:%M:%S")} ERROR [db] '
                    f'Query timeout ao consultar deputado {dep["nome_eleitoral"]} '
                    f'(CPF: {dep["cpf"]}, gabinete {dep["gabinete"]}) - '
                    f'Connection pool exhausted: '
                    f'postgresql://api_readonly@db-prod-legislativo.camara.gov.br:5432/legislativo_prod'
                )

    content = "\n".join(lines) + "\n"
    path = DATA_DIR / "api_access_camara.log"
    path.write_text(content, encoding="utf-8")
    print(f"  LOG: {path} ({len(lines)} linhas)")
    return path


# ─── 5. VCF ───────────────────────────────────────────────────────────────

def gerar_vcf():
    vcards = []
    for d in DEPUTADOS_DETALHADOS:
        partes = d["nome_civil"].split()
        sobrenome = partes[-1]
        nomes = " ".join(partes[:-1])

        vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{d['nome_civil']}
N:{sobrenome};{nomes};;;
NICKNAME:{d['nome_eleitoral']}
EMAIL;TYPE=WORK:{d['email']}
TEL;TYPE=WORK,VOICE:{d['telefone']}
ORG:Câmara dos Deputados;{d['partido']}/{d['uf']}
TITLE:Deputado Federal
ADR;TYPE=WORK:;;Praça dos Três Poderes - Anexo {d['predio']}, Gabinete {d['gabinete']};Brasília;DF;70160-900;Brasil
BDAY:{d['nascimento']}
NOTE:CPF: {d['cpf']}. Naturalidade: {d['naturalidade']}. Escolaridade: {d['escolaridade']}. 57ª Legislatura (2023-2027).
URL:https://www.camara.leg.br/deputados/{d['nome_eleitoral'].lower().replace(' ', '-')}
CATEGORIES:Deputado Federal,{d['partido']},{d['uf']}
REV:{datetime.now().strftime("%Y%m%dT%H%M%SZ")}
END:VCARD"""
        vcards.append(vcard)

    # Adicionar mais contatos da lista simples
    for nome, partido, uf, email in DEPUTADOS_LISTA[5:25]:
        partes = nome.split()
        sobrenome = partes[-1] if len(partes) > 1 else nome
        nomes = " ".join(partes[:-1]) if len(partes) > 1 else nome
        tel = f"(61) 3215-{random.randint(5000,5999)}"

        vcard = f"""BEGIN:VCARD
VERSION:3.0
FN:{nome}
N:{sobrenome};{nomes};;;
EMAIL;TYPE=WORK:{email}
TEL;TYPE=WORK,VOICE:{tel}
ORG:Câmara dos Deputados;{partido}/{uf}
TITLE:Deputado Federal
ADR;TYPE=WORK:;;Praça dos Três Poderes - Anexo 4;Brasília;DF;70160-900;Brasil
NOTE:Partido {partido}, UF: {uf}. 57ª Legislatura. Contato institucional.
CATEGORIES:Deputado Federal,{partido},{uf}
REV:{datetime.now().strftime("%Y%m%dT%H%M%SZ")}
END:VCARD"""
        vcards.append(vcard)

    content = "\n".join(vcards) + "\n"
    path = DATA_DIR / "contatos_deputados.vcf"
    path.write_text(content, encoding="utf-8")
    print(f"  VCF: {path} ({len(vcards)} contatos)")
    return path


# ─── 6. PARQUET ───────────────────────────────────────────────────────────

def gerar_parquet():
    import pandas as pd

    records = []
    for d in DEPUTADOS_DETALHADOS:
        records.append({
            "nome_civil": d["nome_civil"],
            "nome_eleitoral": d["nome_eleitoral"],
            "cpf": d["cpf"],
            "data_nascimento": d["nascimento"],
            "naturalidade": d["naturalidade"],
            "escolaridade": d["escolaridade"],
            "partido": d["partido"],
            "uf": d["uf"],
            "email": d["email"],
            "telefone": d["telefone"],
            "gabinete": d["gabinete"],
            "salario_bruto": round(random.uniform(33000, 44000), 2),
            "verba_gabinete": round(random.uniform(80000, 111000), 2),
            "cota_parlamentar": round(random.uniform(30000, 50000), 2),
        })

    for nome, partido, uf, email in DEPUTADOS_LISTA[5:]:
        cpf = f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"
        nasc = f"{random.randint(1955,1995)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        records.append({
            "nome_civil": nome,
            "nome_eleitoral": nome,
            "cpf": cpf,
            "data_nascimento": nasc,
            "naturalidade": "",
            "escolaridade": random.choice(["Superior", "Pós-graduação", "Mestrado", "Doutorado"]),
            "partido": partido,
            "uf": uf,
            "email": email,
            "telefone": f"(61) 3215-{random.randint(5000,5999)}",
            "gabinete": str(random.randint(100, 999)),
            "salario_bruto": round(random.uniform(33000, 44000), 2),
            "verba_gabinete": round(random.uniform(80000, 111000), 2),
            "cota_parlamentar": round(random.uniform(30000, 50000), 2),
        })

    df = pd.DataFrame(records)
    path = DATA_DIR / "cadastro_deputados.parquet"
    df.to_parquet(path, index=False, engine="pyarrow")
    print(f"  PARQUET: {path} ({len(df)} registros, {len(df.columns)} colunas)")
    return path


# ─── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Gerando 6 arquivos de teste com dados reais da Câmara dos Deputados...\n")
    gerar_html()
    gerar_yaml()
    gerar_sql()
    gerar_log()
    gerar_vcf()
    gerar_parquet()
    print("\nTodos os arquivos gerados em:", DATA_DIR)
