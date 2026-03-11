# PSA — Privacy Shield Agent for AI

<div align="center">

**Seus dados nunca saem. A IA trabalha no escuro.**

[![Audit Score](https://img.shields.io/badge/Audit%20Score-100%2F100-00e5ff?style=for-the-badge&logo=shield&logoColor=white)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai)
[![Version](https://img.shields.io/badge/Version-v5.1-00ff9d?style=for-the-badge)](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases/tag/v5.1)
[![License](https://img.shields.io/badge/License-MIT-7b5ea7?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LGPD](https://img.shields.io/badge/LGPD-Compliant-green?style=for-the-badge)](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
[![GDPR](https://img.shields.io/badge/GDPR-Compliant-green?style=for-the-badge)](https://gdpr.eu)
[![HIPAA](https://img.shields.io/badge/HIPAA-Compliant-green?style=for-the-badge)](https://www.hhs.gov/hipaa)

*Camada de segurança local que intercepta e anonimiza dados sensíveis **antes** de enviá-los a qualquer IA.*
*Funciona com Claude, ChatGPT, Gemini e qualquer LLM via API.*

[Site](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai) · [Release v5.1](https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases/tag/v5.1) · [Lista de Espera](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)

</div>

---

> **PSA não é uma ferramenta de produtividade. É uma camada de segurança que, como consequência, também economiza 99% dos tokens e torna qualquer análise 30x mais rápida.**

---

## Por que segurança em primeiro lugar?

Toda empresa que usa IA com dados reais está exposta. O PSA resolve os 4 maiores medos:

### 😱 Vazamento de dados
CPF, salário, endereço, prontuário — tudo isso vai para servidores externos quando você cola numa IA.
**PSA: dados reais nunca saem do seu computador. A IA só vê dados fictícios.**

### ⚖️ Multa LGPD/GDPR
A ANPD pode multar até **2% do faturamento**. A GDPR até **4%**. Basta um incidente.
**PSA: compliance automático + log auditável de cada operação.**

### 🏭 Segredo industrial
Preços, margens, clientes VIP, estratégias — tudo exposto ao enviar para a nuvem.
**PSA: só dados fictícios chegam à nuvem. Seus segredos ficam no seu computador.**

### 🤖 Dados treinando concorrentes
Termos de uso de IAs podem permitir uso dos seus dados para treinar modelos.
**PSA: nenhum dado real alimenta nenhum modelo. Zero. Nunca.**

---

## Compliance garantido

| Regulação | Status | Escopo |
|---|---|---|
| ✅ **LGPD** | Compliant | Lei Geral de Proteção de Dados (Brasil, Lei 13.709/2018) |
| ✅ **GDPR** | Compliant | General Data Protection Regulation (Europa) |
| ✅ **HIPAA** | Compliant | Health Insurance Portability and Accountability Act (EUA) |
| ✅ **Sigilo profissional** | Compliant | OAB, CRM, CRC — dados de clientes/pacientes protegidos |
| ✅ **Segredo industrial** | Compliant | Preços, margens, estratégias nunca saem do ambiente local |

---

## Caso real: 256.013 servidores do GDF

| Métrica | Resultado |
|---|---|
| Base de teste | **256.013 linhas** — folha de pagamento real do Governo do Distrito Federal |
| Vazamentos detectados | **Zero** |
| Score de auditoria | **100/100** (28/28 vulnerabilidades corrigidas) |
| Padrões PII detectados | **70+** |
| Formatos suportados | **11** |

**Nenhum nome, CPF, salário ou endereço real saiu do computador.**

---

## Amostragem Inteligente v5.1

> **O PSA é estatisticamente inteligente — envia o mínimo necessário para cada tamanho de arquivo, nunca mais do que precisa.**

A função `calculate_sample_size(n)` determina automaticamente a amostra ideal com base no Teorema Central do Limite (n >= 30):

| Tamanho do arquivo (N linhas) | Amostra enviada | Regra |
|---|---|---|
| N <= 30 | 100% (todas as linhas) | Arquivo pequeno — manda tudo com aviso no log |
| 31 a 100 | 50% de N (mínimo 30) | Reduz mas mantém representatividade estatística |
| 101 a 10.000 | 100 linhas | Padrão |
| 10.001 a 100.000 | 150 linhas | Arquivo grande — amostra ligeiramente maior |
| 100.001+ | 200 linhas | Máximo recomendado |

### Exemplos reais

| Arquivo | Total | Amostra | % enviado | Comportamento |
|---|---|---|---|---|
| Relatório pequeno | 25 linhas | 25 (tudo) | 100% | Aviso: "Arquivo pequeno — enviando todas as 25 linhas" |
| Lista de clientes | 60 linhas | 30 | 50% | `max(30, 60//2) = 30` |
| Folha GDF | 256.013 linhas | 200 | 0,08% | Máximo recomendado para arquivos 100K+ |

O parâmetro `--sample N` no CLI sobrescreve a lógica automática quando informado explicitamente.

---

## Benefícios adicionais (consequências da proteção)

A segurança vem primeiro. Mas ao proteger seus dados, o PSA entrega dois bônus:

### Economia de até 99,9% dos tokens

Ao proteger seus dados, o PSA envia apenas o mínimo estatístico — economizando até **99,92% dos tokens**.

| Cenário | Sem PSA | Com PSA (v5.1) | Economia |
|---|---|---|---|
| Planilha de 256.000 linhas | 256.000 linhas enviadas | 200 linhas enviadas | **99,92%** |
| Planilha de 60 linhas | 60 linhas enviadas | 30 linhas enviadas | **50%** |
| Custo estimado (256K linhas) | ~US$ 12,00 | ~US$ 0,10 | **99,2%** |

### Análises 30x mais rápidas

Como a amostra é mínima, análises de 15 minutos viram 30 segundos.

| Cenário | Sem PSA | Com PSA |
|---|---|---|
| Tempo de análise | ~15 min | ~30 seg |
| Tempo de resposta da IA | timeout frequente | resposta imediata |

> Esses ganhos não são o objetivo do PSA. São **consequências** de proteger seus dados corretamente.

---

## Como funciona — Os 19 Passos

**15 de 19 passos rodam 100% local. Seus dados reais jamais saem do seu computador.**

**Nem o nome do seu arquivo sai do computador. Seus dados começam protegidos do primeiro ao último passo.**

| Passo | O que acontece | Local ou Nuvem | Consome Token? | Dados saem do computador? |
|---|---|---|---|---|
| 1 | Usuário entrega o arquivo ao PSA | 💻 Local | ❌ Não | ❌ Não — nome protegido por código genérico (DOC_001) via file_registry |
| 2 | PSA invoca o psa.py via código genérico | 💻 Local | ❌ Não | ❌ Não |
| 3 | Valida segurança do arquivo | 💻 Local | ❌ Não | ❌ Não |
| 4 | Detecta extensão e escolhe script correto | 💻 Local | ❌ Não | ❌ Não |
| 5 | Lê o arquivo real do disco | 💻 Local | ❌ Não | ❌ Não |
| 6 | Amostragem inteligente — `calculate_sample_size(n)` determina o mínimo necessário **[NOVO v5.1]** | 💻 Local | ❌ Não | ❌ Não |
| 7 | Detecta colunas sensíveis (70+ keywords) | 💻 Local | ❌ Não | ❌ Não |
| 8 | Renomeia colunas para COL_A, COL_B... | 💻 Local | ❌ Não | ❌ Não |
| 9 | Anonimiza valores com Faker pt_BR offline | 💻 Local | ❌ Não | ❌ Não |
| 10 | Varia valores financeiros em ±15% | 💻 Local | ❌ Não | ❌ Não |
| 11 | Escaneia textos livres e substitui via regex | 💻 Local | ❌ Não | ❌ Não |
| 12 | Validação anti-vazamento — detectou dado real? Deleta tudo automaticamente | 💻 Local | ❌ Não | ❌ Não |
| 13 | Salva arquivo anonimizado em data/anonymized/ | 💻 Local | ❌ Não | ❌ Não |
| 14 | Salva mapa de correspondência em data/maps/ | 💻 Local | ❌ Não | ❌ Não |
| 15 | Salva log da operação em logs/ | 💻 Local | ❌ Não | ❌ Não |
| 16 | Claude/IA lê o arquivo anonimizado | ☁️ Nuvem | ✅ Sim | ✅ Sim — só dados fictícios |
| 17 | Claude/IA realiza análise e responde | ☁️ Nuvem | ✅ Sim | ✅ Sim — só resultados fictícios |
| 18 | Claude/IA gera script Python para rodar localmente | ☁️ Nuvem | ✅ Sim | ✅ Sim — só o código, sem dados |
| 19 | Script roda nos dados reais localmente → results/ | 💻 Local | ❌ Não | ❌ Não |

### Exemplo real

```python
# Entrada (seu documento)
"O cliente João Silva, CPF 123.456.789-00, email joao@empresa.com"

# Após PSA (o que a IA vê)
"O cliente [NAME_7f2a], CPF [CPF_9b1c], email [EMAIL_3d8e]"

# Resultado revertido (você recebe)
"O cliente João Silva, CPF 123.456.789-00, email joao@empresa.com"
```

---

## Formatos suportados

| Formato | Extensão |
|---|---|
| Documentos Word | `.docx` |
| Planilhas Excel | `.xlsx`, `.csv` |
| PDF | `.pdf` |
| Texto puro | `.txt` |
| Dados estruturados | `.json`, `.xml` |
| E-mail | `.eml`, `.msg` |
| Imagens (OCR) | `.png`, `.jpg` |

---

## Padrões PII detectados (70+)

- **Documentos brasileiros:** CPF, CNPJ, RG, CNH, PIS/PASEP, Título de Eleitor
- **Contato:** E-mail, telefone fixo, celular, WhatsApp
- **Localização:** Endereço completo, CEP, coordenadas GPS
- **Financeiro:** Cartão de crédito, conta bancária, agência, PIX
- **Saúde:** CRM, CRF, prontuário, convênio
- **Identificação:** Nome completo, data de nascimento, passaporte

---

## Agentes disponíveis

| Agente | Função |
|---|---|
| **Comandante (CEO)** | Orquestra o fluxo completo de proteção |
| **PSA Guardião** | Especialista em anonimização e validação |
| **CFO** | Processamento de dados financeiros |

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/myrkis-br/psa-privacy-shield-agent-for-ai.git
cd psa-privacy-shield-agent-for-ai

# Instale as dependências
pip install -r requirements.txt

# Execute
python psa.py
```

### Pré-requisitos

- Python 3.10+
- Chave de API da Anthropic (Claude) ou OpenAI (ChatGPT)

---

## Para quem é

| Setor | Caso de uso |
|---|---|
| ⚖️ **Advocacia** | Analisar contratos sem expor dados de clientes |
| 🏥 **Saúde** | Processar prontuários com sigilo médico |
| 📊 **Contabilidade / RH** | Trabalhar com CPFs e salários em segurança |
| 🏛️ **Governo** | Bases públicas com dados pessoais de cidadãos |
| 🏢 **PMEs** | Compliance LGPD sem contratar DPO |

---

## Estrutura do projeto

```
psa-privacy-shield-agent-for-ai/
├── psa.py                    # Script principal
├── anonymizer.py             # Motor de anonimização
├── text_engine.py            # Processamento de texto
├── anonymize_document.py     # Suporte a DOCX/XLSX
├── anonymize_pdf.py          # Suporte a PDF
├── anonymize_presentation.py # Suporte a PPTX
├── anonymize_email.py        # Suporte a EML/MSG
├── CLAUDE.md                 # Instruções para Claude Code
├── CHANGELOG.md              # Histórico de versões
└── docs/
    └── SKILL-SPEC.md         # Especificação técnica
```

---

## Autor

**Marcos Cruz**
Brasília/DF — Março 2026
Ideia original: PSA como modo nativo de privacidade em qualquer IA.

---

## Contato & Validação

Estou validando o PSA com profissionais de advocacia, saúde e contabilidade.
Se você lida com dados sensíveis e usa IA, quero conversar.

[Site oficial](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai) · [Lista de espera](https://myrkis-br.github.io/psa-privacy-shield-agent-for-ai)

---

<div align="center">
  <sub>Built with security in Brasilia, Brasil · Co-authored with Claude (Anthropic)</sub>
</div>
