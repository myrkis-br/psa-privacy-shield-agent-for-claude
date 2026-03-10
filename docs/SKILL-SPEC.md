# PSA — Privacy Shield Agent
## Especificação Técnica para Skill / Integração Claude

---

## Visão Geral

O PSA é uma camada de proteção local que intercepta, anonimiza e protege dados sensíveis antes que sejam expostos a LLMs ou serviços externos. Roda 100% local — nenhum dado real sai do computador.

**Problema**: Usuários precisam analisar dados sensíveis (planilhas de RH, contratos, relatórios financeiros) com ajuda de IA, mas não podem expor PII.

**Solução**: O PSA anonimiza automaticamente, preservando a estrutura dos dados para análise, e gera código que opera nos dados reais localmente.

---

## Arquitetura

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Usuário     │────▶│  Comandante  │────▶│  PSA Guardião   │
│  (pedido)    │     │  (Claude)    │     │  (anonimização) │
└─────────────┘     └──────┬───────┘     └────────┬────────┘
                           │                      │
                           │  dados anonimizados   │
                           │◀─────────────────────┘
                           │
                    ┌──────▼───────┐     ┌─────────────────┐
                    │  Análise     │────▶│  Código gerado   │
                    │  (anonimiz.) │     │  (dados reais)   │
                    └──────────────┘     └─────────────────┘
                                          execução local
```

---

## Fluxo de 4 Etapas

1. **Interceptar** — Arquivo do usuário chega ao PSA
2. **Anonimizar** — Detecta e substitui PII (nomes, CPF, CNPJ, valores, endereços, etc.)
3. **Analisar** — Claude trabalha com dados anonimizados
4. **Entregar** — Gera código Python que acessa dados reais para execução local

---

## Scripts

| Script | Função |
|--------|--------|
| `psa.py` | Interface unificada — ponto de entrada único |
| `anonymizer.py` | Planilhas CSV/XLSX — detecção de colunas + text_engine em texto livre |
| `text_engine.py` | Motor de regex — CPF, CNPJ, RG, PIS, nomes (mixed/ALL-CAPS), endereços, datas, valores |
| `anonymize_document.py` | DOCX/TXT — headers/footers, encoding fallback |
| `anonymize_pdf.py` | PDF via pdfplumber — tabelas, aviso OCR |
| `anonymize_presentation.py` | PPTX — slides com shapes e tabelas |
| `anonymize_email.py` | EML/MSG — campos, corpo, aviso sobre anexos |

---

## Formatos Suportados

| Formato | Extensões | Amostragem |
|---------|-----------|------------|
| Planilhas | `.csv` `.xlsx` `.xls` | N linhas (padrão: 100) |
| Documentos | `.docx` `.txt` | N parágrafos (padrão: 20) |
| PDFs | `.pdf` | N páginas (padrão: 10) |
| Apresentações | `.pptx` | N slides (padrão: 15) |
| Emails | `.eml` `.msg` | Completo (campo a campo) |

---

## Entidades Detectadas

- **Documentos**: CPF, CNPJ, RG, PIS/PASEP/NIS, CTPS, CNH
- **Contato**: Email, telefone, CEP, endereço
- **Pessoal**: Nomes (Mixed Case + ALL-CAPS + honoríficos + sufixos)
- **Financeiro**: Valores monetários (R$), salários, coordenadas
- **Temporal**: Datas BR e ISO, processos judiciais
- **Planilhas**: 70+ keywords sensíveis com detecção automática de tipo

---

## Requisitos

- **Python**: 3.9+
- **Dependências**: `pandas`, `faker`, `pdfplumber`, `python-docx`, `python-pptx`, `openpyxl`
- **SO**: macOS / Linux (Windows não testado)
- **Armazenamento**: ~50MB para dependências

---

## Instalação e Uso

```bash
# Clonar / copiar o projeto
cd psa-project

# Instalar dependências
pip3 install pandas faker pdfplumber python-docx python-pptx openpyxl

# Anonimizar um arquivo
python3 scripts/psa.py data/real/planilha.xlsx

# Anonimizar uma pasta inteira
python3 scripts/psa.py data/real/

# Ver formatos suportados
python3 scripts/psa.py --list-supported
```

Saída em `data/anonymized/` (arquivo anonimizado) e `data/maps/` (mapa de correspondência).

---

## Proposta de Integração como Skill

### Nome: `psa` ou `privacy-shield`

### Trigger
Quando o usuário fornece um arquivo para análise que pode conter dados sensíveis.

### Comportamento
1. Skill detecta tipo de arquivo e executa `psa.py` automaticamente
2. Lê o resultado anonimizado e apresenta ao Claude para análise
3. Claude trabalha exclusivamente com dados anonimizados
4. Código de saída referencia `data/real/` para execução local

### Comandos de Skill
```
/psa <arquivo>           — anonimiza e analisa
/psa --scan <pasta>      — processa pasta inteira
/psa --audit             — roda auditoria de segurança
/psa --status            — mostra arquivos processados
```

### Regras de Protocolo (CLAUDE.md)
O CLAUDE.md na raiz do projeto define regras que o Claude segue automaticamente:
- Nunca ler `data/real/`, `data/maps/`, `data/samples/`, `logs/`
- Sempre executar PSA antes de analisar dados
- Gerar código que acessa dados reais para execução local
- Bloquear saída em caso de vazamento detectado

### Valor para o Ecossistema
- **Privacidade por design** — dados reais nunca saem do computador
- **Compatível com qualquer LLM** — a anonimização é pré-processamento
- **Auditável** — logs estruturados e relatórios de segurança
- **Extensível** — novos formatos adicionáveis via padrão dispatcher
