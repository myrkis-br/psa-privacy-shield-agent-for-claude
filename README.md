<p align="center">
  <h1 align="center">PSA — Privacy Shield Agent for Claude</h1>
  <p align="center">Camada de proteção local que anonimiza dados sensíveis antes de enviá-los a LLMs</p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Auditoria-100%2F100-brightgreen?style=for-the-badge" alt="Auditoria 100/100">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/LGPD-Compliant-green?style=for-the-badge" alt="LGPD">
  <img src="https://img.shields.io/badge/Licença-MIT-yellow?style=for-the-badge" alt="MIT License">
</p>

---

## O Problema

Você precisa analisar planilhas de RH, contratos, relatórios financeiros com ajuda de IA — mas não pode expor CPF, nomes, salários e outros dados pessoais.

## A Solução

O **PSA** intercepta seus arquivos, anonimiza automaticamente todos os dados sensíveis e entrega uma versão segura para o Claude (ou qualquer LLM) analisar. Os dados reais **nunca saem do seu computador**.

```
Usuário → PSA Guardião (anonimiza) → Claude (analisa dados fake) → Código (roda nos dados reais localmente)
```

## Funcionalidades

- **7 formatos suportados**: CSV, XLSX, XLS, DOCX, TXT, PDF, PPTX, EML, MSG
- **70+ keywords sensíveis** detectadas automaticamente em planilhas
- **Entidades detectadas**: CPF, CNPJ, RG, PIS/PASEP, CTPS, nomes (Mixed Case + ALL-CAPS + honoríficos), emails, telefones, endereços, CEP, valores monetários, datas, coordenadas
- **Validação anti-vazamento**: bloqueia a saída se detectar dados reais no arquivo anonimizado
- **Amostragem inteligente**: processa N linhas/páginas/parágrafos/slides para arquivos grandes
- **Integração com Claude Code**: regras de protocolo via `CLAUDE.md` garantem que o Claude nunca acesse dados reais

## Instalação

```bash
# Clone o repositório
git clone https://github.com/myrkis-br/psa-privacy-shield-agent-for-claude.git
cd psa-privacy-shield-agent-for-claude

# Instale as dependências
pip3 install pandas faker pdfplumber python-docx python-pptx openpyxl
```

## Uso

```bash
# Anonimizar um arquivo
python3 scripts/psa.py data/real/planilha.xlsx

# Anonimizar com amostragem
python3 scripts/psa.py data/real/planilha.xlsx --sample 50
python3 scripts/psa.py data/real/relatorio.pdf --pages 5
python3 scripts/psa.py data/real/contrato.docx --paragraphs 15

# Anonimizar uma pasta inteira
python3 scripts/psa.py data/real/

# Ver formatos suportados
python3 scripts/psa.py --list-supported
```

**Saída:**
- `data/anonymized/` — arquivo anonimizado (seguro para LLMs)
- `data/maps/` — mapa de correspondência real↔fake (protegido, nunca sai do computador)

## Com o Claude Code

Coloque seus arquivos em `data/real/` e peça ao Claude para analisar. O `CLAUDE.md` na raiz do projeto define regras automáticas:

1. Claude detecta que o arquivo está em `data/real/`
2. Executa o PSA Guardião para anonimizar
3. Lê apenas a versão anonimizada
4. Gera código que roda nos dados reais **localmente**

O Claude **nunca** lê `data/real/`, `data/maps/`, `data/samples/` ou `logs/`.

## Estrutura do Projeto

```
psa-project/
├── agents/                     # Definição dos agentes (Comandante, Guardião, CFO)
├── data/
│   ├── real/                   # ⛔ Dados reais — NUNCA saem do computador
│   ├── anonymized/             # ✅ Dados anonimizados — seguros para LLMs
│   ├── maps/                   # ⛔ Mapas real↔fake — protegidos
│   └── samples/                # ⛔ Amostras pré-anonimização
├── scripts/
│   ├── psa.py                  # Interface unificada (ponto de entrada)
│   ├── text_engine.py          # Motor de regex (CPF, CNPJ, nomes, etc.)
│   ├── anonymizer.py           # Planilhas CSV/XLSX
│   ├── anonymize_document.py   # Documentos DOCX/TXT
│   ├── anonymize_pdf.py        # PDFs
│   ├── anonymize_presentation.py # Apresentações PPTX
│   └── anonymize_email.py      # Emails EML/MSG
├── results/                    # Resultados de análises
├── logs/                       # ⛔ Logs protegidos
├── CLAUDE.md                   # Regras de protocolo para o Claude
└── CHANGELOG.md                # Histórico de versões
```

## Segurança

| Proteção | Descrição |
|----------|-----------|
| **Anti-vazamento** | Valida saída e BLOQUEIA + DELETA se detectar dados reais |
| **Seed entrópico** | `os.urandom()` a cada execução (não determinístico) |
| **SHA-256** | Cache de anonimização usa hash seguro |
| **Text engine** | Escaneia colunas de texto livre em planilhas |
| **ALL-CAPS** | Detecta nomes em MAIÚSCULAS (comum em documentos oficiais BR) |
| **Honoríficos** | Dr., Dra., Sr., Sra., Prof., Des., Min. |
| **Encoding** | Auto-detecta UTF-8, Latin-1, CP1252 |
| **CLAUDE.md** | Regras automáticas impedem o Claude de acessar dados reais |

### Auditoria de Segurança

| Versão | Score | Vulnerabilidades |
|--------|-------|------------------|
| v1 | 62/100 — REPROVADO | 28 abertas (3 críticas) |
| **v2** | **100/100 — APROVADO** | **28/28 corrigidas** |

## Requisitos

- Python 3.9+
- macOS / Linux
- Dependências: `pandas`, `faker`, `pdfplumber`, `python-docx`, `python-pptx`, `openpyxl`

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

<p align="center">
  Desenvolvido por <strong>Marcos Cruz</strong> — Brasília/DF, Brasil<br>
  Março 2026
</p>
