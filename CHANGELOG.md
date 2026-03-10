# Changelog — PSA (Privacy Shield Agent)

## [2.0.0] — 2026-03-10

### Auditoria de Segurança
- **v1**: Score 62/100 — REPROVADO CONDICIONAL (28 vulnerabilidades abertas)
- **v2**: Score 100/100 — APROVADO (28/28 corrigidas)

### Correções CRÍTICAS
- **C-01**: `_validate_no_leakage` agora BLOQUEIA saída, DELETA arquivo e levanta `LeakageError`
- **C-02**: `text_engine` aplicado em colunas de texto livre de planilhas (detecção automática)
- **C-03**: Regex de nomes reescrito — ALL-CAPS, honoríficos (Dr./Dra./Sr./Prof./Des./Min.), sufixos (Filho/Junior/Neto)

### Correções ALTAS (10)
- Seed aleatório via `os.urandom(8)` (não mais `Faker.seed(42)`)
- 30+ keywords sensíveis adicionadas (pis, pasep, ctps, bruto, líquido, lat/lng, etc.)
- Word-boundary match para keywords curtas (rg, uf, tel)
- Type hints corrigidos para Python 3.9
- Regex para RG, PIS/PASEP/NIS, CTPS, endereços
- DOCX: extração de headers/footers
- TXT: fallback de encoding (utf-8 → latin-1 → cp1252)
- Email: aviso sobre conteúdo de anexos não escaneado
- `_security_check` expandido (bloqueia maps/, samples/, logs/, anonymized/)
- Security check aplicado em processamento de pastas

### Correções MÉDIAS (14) e BAIXAS (1)
- `_NOT_A_NAME` expandido (26 estados, instituições, termos financeiros)
- Datas ISO (2024-01-31) detectadas
- MD5 → SHA-256 para cache keys
- PII removida de logs (tokens apenas, nunca originais)
- PDF: default 10 páginas, erros de tabela logados, aviso para PDFs escaneados
- HTML entities: `html.unescape()` em vez de subset manual
- CLAUDE.md: contradição Seção 4 vs 5 resolvida, logs/ protegido, seção técnica adicionada
- Coordenadas lat/lng anonimizadas (±0.05 graus)

### Arquivos Modificados
- `scripts/text_engine.py` — motor de regex reescrito
- `scripts/anonymizer.py` — bloqueio de vazamento, text_engine em texto livre, keywords expandidas
- `scripts/psa.py` — security check expandido, default PDF 10 páginas
- `scripts/anonymize_document.py` — headers/footers, encoding fallback, logs sem PII
- `scripts/anonymize_email.py` — aviso anexos, logs sem PII, html.unescape()
- `scripts/anonymize_pdf.py` — default 10 pags, erros logados, aviso OCR
- `CLAUDE.md` — contradições resolvidas, logs/ protegido, seção técnica

### Arquivos Criados
- `results/auditoria_psa.html` — relatório v1 (62/100)
- `results/auditoria_psa_v2.html` — relatório v2 (100/100)
- `scripts/gerar_auditoria_v2.py` — gerador do relatório v2

---

## [1.0.0] — 2026-03-10

### Criação do Projeto
- Estrutura de diretórios (data/real, anonymized, maps, samples)
- `scripts/anonymizer.py` — anonimizador de CSV/XLSX
- `scripts/text_engine.py` — motor de regex para texto livre
- `scripts/anonymize_document.py` — DOCX/TXT
- `scripts/anonymize_pdf.py` — PDF via pdfplumber
- `scripts/anonymize_presentation.py` — PPTX
- `scripts/anonymize_email.py` — EML/MSG
- `scripts/psa.py` — interface unificada
- `scripts/test_anonymizer.py` — teste ponta a ponta
- `CLAUDE.md` — regras de protocolo
- `agents/` — definições de agentes (comandante, psa-guardião, cfo)

### Análises GDF
- `scripts/analise_completa_gdf.py` — análise de remuneração com teto STF, acúmulo de cargos, classificação legal
- `scripts/analise_folha_por_orgao.py` — top 5 órgãos por folha de pagamento
- `results/analise_remuneracao_gdf.html` — relatório completo
