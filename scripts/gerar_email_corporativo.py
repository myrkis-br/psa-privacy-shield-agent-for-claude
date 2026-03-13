"""
Gera um arquivo .eml corporativo realista com dados fictícios
para teste do PSA Guardião.
"""
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from pathlib import Path
from datetime import datetime

_TEST_TOKEN = os.environ.get("PSA_TEST_API_TOKEN", "FAKE_TOKEN_PLACEHOLDER")

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "real" / "proposta_comercial_nexus.eml"

# --- Montagem do email ---
msg = MIMEMultipart("mixed")

msg["From"] = "Ricardo Almeida Fonseca <ricardo.fonseca@nexuscapital.com.br>"
msg["To"] = (
    "Ana Carolina Duarte <ana.duarte@grupoatlas.com.br>, "
    "Pedro Henrique Machado <pedro.machado@grupoatlas.com.br>"
)
msg["CC"] = (
    "Fernanda Oliveira Santos <fernanda.santos@nexuscapital.com.br>, "
    "Juliana Reis Monteiro <juliana.monteiro@grupoatlas.com.br>"
)
msg["Subject"] = "Proposta Comercial - Projeto Integração ERP Atlas/Nexus - CONFIDENCIAL"
msg["Date"] = "Wed, 11 Mar 2026 09:47:22 -0300"
msg["Message-ID"] = "<20260311094722.8A3F2@mail.nexuscapital.com.br>"
msg["Reply-To"] = "comercial@nexuscapital.com.br"
msg["X-Priority"] = "1"

body = """\
Prezada Dra. Ana Carolina,

Conforme alinhado na reunião de 05/03/2026 em nosso escritório na
Av. Paulista, 1578, 22° andar, Bela Vista, São Paulo/SP, CEP 01310-200,
segue a proposta comercial revisada para o Projeto de Integração ERP
Atlas/Nexus.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DADOS DO CONTRATANTE:
  Razão Social: Grupo Atlas Participações S.A.
  CNPJ: 12.345.678/0001-90
  Inscrição Estadual: 123.456.789.012
  Endereço: Rua Augusta, 2.840, Cerqueira César, São Paulo/SP
  CEP: 01412-100
  Responsável Técnico: Eng. Pedro Henrique Machado
  CPF: 123.456.789-00
  RG: 34.567.890-1 SSP/SP
  Telefone: (11) 3845-7200

DADOS DO CONTRATADO:
  Razão Social: Nexus Capital Tecnologia Ltda.
  CNPJ: 98.765.432/0001-10
  Inscrição Estadual: 987.654.321.098
  Endereço: Av. Paulista, 1578, Bela Vista, São Paulo/SP
  CEP: 01310-200
  Responsável Comercial: Ricardo Almeida Fonseca
  CPF: 987.654.321-00
  RG: 12.345.678-9 SSP/SP
  Telefone: (11) 2198-4500

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESUMO FINANCEIRO DA PROPOSTA:

  Fase 1 - Diagnóstico e Mapeamento:       R$ 185.000,00
  Fase 2 - Desenvolvimento e Integração:    R$ 742.500,00
  Fase 3 - Testes e Homologação:            R$ 298.000,00
  Fase 4 - Implantação e Go-Live:           R$ 425.750,00
  Fase 5 - Suporte Pós-Implantação (12m):   R$ 156.000,00
  ─────────────────────────────────────────────────────────
  VALOR TOTAL DO PROJETO:                 R$ 1.807.250,00
  Desconto comercial (5%):                 -R$ 90.362,50
  VALOR FINAL:                            R$ 1.716.887,50

  Condições de pagamento: 30% na assinatura + 6 parcelas mensais
  Conta para depósito:
    Banco Itaú (341) | Agência 0987 | CC 12345-6
    Titular: Nexus Capital Tecnologia Ltda.
    CNPJ: 98.765.432/0001-10
    Chave PIX: financeiro@nexuscapital.com.br

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EQUIPE DO PROJETO (Nexus):

  Gerente de Projeto: Marcos Vinícius Teixeira
    CPF: 456.789.123-45 | Email: marcos.teixeira@nexuscapital.com.br
    Cel: (11) 98765-4321

  Arquiteto de Soluções: Dr. Felipe Augusto Barros
    CPF: 321.654.987-00 | Email: felipe.barros@nexuscapital.com.br
    Cel: (11) 97654-3210

  Analista Sênior: Camila Rodrigues Pinto
    CPF: 654.321.789-12 | Email: camila.pinto@nexuscapital.com.br

EQUIPE DO PROJETO (Atlas):

  Coordenadora de TI: Juliana Reis Monteiro
    CPF: 789.123.456-78 | Email: juliana.monteiro@grupoatlas.com.br
    Cel: (11) 99876-5432

  DBA Sênior: Roberto Carlos Mendes
    CPF: 147.258.369-00 | Email: roberto.mendes@grupoatlas.com.br

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DADOS SENSÍVEIS DOS SERVIDORES:

  Servidor de Produção Atlas:
    IP: 192.168.15.100
    Usuário admin: atlas_admin
    Banco: Oracle 19c | SID: ATLPROD
    Porta: 1521

  Servidor Nexus (Homologação):
    IP: 10.0.0.50
    API Gateway: https://api-hml.nexuscapital.com.br
    Token de acesso: {test_token}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Esta proposta tem validade até 31/03/2026.

Solicito que a análise jurídica seja conduzida pelo escritório
Monteiro, Bastos & Advogados Associados (OAB/SP 12345), sob
responsabilidade da Dra. Patrícia Monteiro Bastos (OAB/SP 98765),
com cópia para patricia.bastos@mbadvogados.com.br.

Fico à disposição para esclarecimentos.

Atenciosamente,

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ricardo Almeida Fonseca
Diretor Comercial | Nexus Capital Tecnologia Ltda.
CNPJ: 98.765.432/0001-10
Av. Paulista, 1578, 22° andar - Bela Vista, São Paulo/SP
Tel: (11) 2198-4500 | Cel: (11) 99887-6543
Email: ricardo.fonseca@nexuscapital.com.br
LinkedIn: linkedin.com/in/ricardofonseca
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AVISO DE CONFIDENCIALIDADE: Esta mensagem e seus anexos contêm
informações confidenciais destinadas exclusivamente ao(s) destinatário(s)
acima indicado(s). Se você recebeu esta mensagem por engano, favor
notificar o remetente e apagar imediatamente. A divulgação, cópia ou
distribuição não autorizada é proibida e sujeita às penalidades da
Lei 13.709/2018 (LGPD) e do Código Penal Brasileiro.
"""

# Corpo em text/plain — injeta credencial fictícia via env var
body = body.format(test_token=_TEST_TOKEN)
msg.attach(MIMEText(body, "plain", "utf-8"))

# Simular anexos (apenas cabeçalho, sem conteúdo real)
for fname in ["Proposta_Comercial_Nexus_Atlas_v3.pdf", "Cronograma_Projeto_ERP.xlsx", "NDA_Nexus_Atlas_2026.docx"]:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(b"[conteudo simulado]")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename=\"{fname}\"")
    msg.attach(part)

# --- Salvar ---
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_bytes(msg.as_bytes())
print(f"EML gerado: {OUTPUT}")
print(f"Tamanho: {OUTPUT.stat().st_size:,} bytes")
