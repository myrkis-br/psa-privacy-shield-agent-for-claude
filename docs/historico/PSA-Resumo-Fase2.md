# PSA — Privacy Shield Agent for AI
## Resumo do Projeto — Fase 2 (atualizado 11/03/2026)

**Autor:** Marcos Cruz — Brasília/DF  
**Tagline:** Seu guarda-costas digital. Seu guardião de dados.

---

## Identidade do Produto

- **Nome completo:** PSA - Privacy Shield Agent for AI
- **Sigla:** PSA
- **Posicionamento principal:** Camada de **segurança** que protege dados sensíveis *antes* de enviá-los a qualquer IA — e como consequência, economiza até 99,96% dos tokens e torna análises 30x mais rápidas
- **Compatível com:** Claude, ChatGPT, Gemini, Llama e qualquer API de IA
- **Público-alvo prioritário:** Advocacia, contabilidade/RH, saúde, governo, PMEs

---

## A Hierarquia Correta de Mensagem

> **1º Segurança** — o maior medo de toda empresa
> **2º Economia de tokens** — consequência da proteção
> **3º Velocidade** — consequência da amostragem mínima

### A frase que resume tudo:
*"PSA não é uma ferramenta de produtividade. É uma camada de segurança que, como consequência, também economiza 99% dos tokens e torna qualquer análise 30x mais rápida."*

---

## Os 4 Medos que o PSA Resolve

| Medo | Problema real | Solução PSA |
|---|---|---|
| 😱 Vazamento de dados de clientes | CPF, salário, endereço vão para servidores externos | Dados reais nunca saem — só fictícios vão à nuvem |
| ⚖️ Multa LGPD/GDPR | ANPD pode multar até 2% do faturamento anual | Compliance automático + log auditável de cada operação |
| 🏭 Segredo industrial | Tabela de preços, clientes VIP e estratégia vão à nuvem | Apenas dados fictícios chegam à nuvem |
| 🤖 Dados treinando concorrentes | Termos de uso de IAs podem usar dados para treinar modelos | Nenhum dado real alimenta nenhum modelo |

---

## Setup Técnico

- Mac Mini M2 8GB dedicado (sem sleep, otimizado)
- Plano Anthropic Max
- Claude Code (versão atual)
- Projeto em `~/psa-project/`
- No Claude Code: `cd ~/psa-project && claude` (CLAUDE.md carrega automaticamente)
- Homebrew instalado, GitHub CLI autenticado como `myrkis-br`

---

## Fase 1 — COMPLETA ✅

- Auditoria: 100/100 APROVADO (28/28 vulnerabilidades corrigidas)
- 5.068+ linhas Python, 12 scripts, 3 agentes, 11 formatos, 70+ keywords
- Teste real: base GDF 256k linhas → amostra inteligente → **zero vazamentos**
- Fluxo: Interceptação → Registro (DOC_NNN) → Amostragem Inteligente → Anonimização → Validação → Execução
- Agentes: Comandante (CEO), PSA Guardião (anonimiza), CFO (financeiro)
- Scripts: psa.py, file_registry.py, anonymizer.py, text_engine.py, anonymize_document/pdf/presentation/email.py
- Docs: CLAUDE.md, CHANGELOG.md, docs/SKILL-SPEC.md

---

## Amostragem Inteligente — v5.1 ✅ NOVO

> *"O PSA é estatisticamente inteligente — envia o mínimo necessário para cada tamanho de arquivo, nunca mais do que precisa."*

A função `calculate_sample_size(n_rows)` determina automaticamente o tamanho ideal da amostra:

| Tamanho do arquivo | Amostra enviada | Lógica |
|---|---|---|
| ≤ 30 linhas | 100% (todas) | Arquivo pequeno — amostragem não faz sentido. Aviso automático no log. |
| 31 a 100 linhas | 50% (mín. 30) | Reduz mas mantém representatividade estatística |
| 101 a 10.000 linhas | 100 linhas | Padrão — mínimo estatisticamente válido com folga |
| 10.001 a 100.000 linhas | 150 linhas | Arquivo grande — amostra ligeiramente maior |
| 100.001+ linhas | 200 linhas | Máximo recomendado |

**Regras importantes:**
- A amostra **nunca** pode ser maior que o arquivo real
- `--sample N` no CLI sobrescreve a lógica automática se o usuário quiser controle manual
- O log registra: tamanho real, tamanho da amostra e % enviado à nuvem
- Base estatística: Teorema Central do Limite — 30 amostras já garantem representatividade

---

## Como o PSA Funciona — Os 19 Passos

> 🛡️ **"15 de 19 passos rodam 100% local. Seus dados reais jamais saem do seu computador."**
> 🛡️ **"Nem o nome do seu arquivo sai do computador."**
> 💰 **Consequência:** economia de até 99,96% dos tokens
> ⚡ **Consequência:** análises de 15 min em 30 segundos

| Passo | O que acontece | Local / Nuvem | Token? | Dados saem? |
|---|---|---|---|---|
| 1 | Nome do arquivo → código genérico (DOC_001) via file_registry | 💻 Local | ❌ Não | ❌ Não |
| 2 | PSA invoca psa.py via código genérico | 💻 Local | ❌ Não | ❌ Não |
| 3 | Valida segurança do arquivo | 💻 Local | ❌ Não | ❌ Não |
| 4 | Detecta extensão e escolhe script correto | 💻 Local | ❌ Não | ❌ Não |
| 5 | Lê o arquivo real do disco | 💻 Local | ❌ Não | ❌ Não |
| 6 | **Amostragem inteligente** — `calculate_sample_size(n)` determina o mínimo necessário | 💻 Local | ❌ Não | ❌ Não |
| 7 | Detecta colunas sensíveis (70+ keywords) | 💻 Local | ❌ Não | ❌ Não |
| 8 | Renomeia colunas para COL_A, COL_B... | 💻 Local | ❌ Não | ❌ Não |
| 9 | Anonimiza valores com Faker pt_BR offline | 💻 Local | ❌ Não | ❌ Não |
| 10 | Varia valores financeiros em ±15% | 💻 Local | ❌ Não | ❌ Não |
| 11 | Escaneia textos livres e substitui via regex | 💻 Local | ❌ Não | ❌ Não |
| 12 | Validação anti-vazamento — detectou dado real? Deleta tudo | 💻 Local | ❌ Não | ❌ Não |
| 13 | Salva arquivo anonimizado em data/anonymized/ | 💻 Local | ❌ Não | ❌ Não |
| 14 | Salva mapa de correspondência em data/maps/ | 💻 Local | ❌ Não | ❌ Não |
| 15 | Salva log (tamanho real, amostra, % enviado) em logs/ | 💻 Local | ❌ Não | ❌ Não |
| 16 | IA lê o arquivo anonimizado | ☁️ Nuvem | ✅ Sim | ✅ Só dados fictícios |
| 17 | IA realiza análise e responde | ☁️ Nuvem | ✅ Sim | ✅ Só resultados fictícios |
| 18 | IA gera script Python para rodar localmente | ☁️ Nuvem | ✅ Sim | ✅ Só o código, sem dados |
| 19 | Script roda nos dados reais localmente → results/ | 💻 Local | ❌ Não | ❌ Não |

---

## Conformidade Garantida

| Regulação | PSA |
|---|---|
| **LGPD** (Brasil) | ✅ Dados pessoais nunca saem sem anonimização |
| **GDPR** (Europa) | ✅ Anonimização antes de qualquer envio |
| **HIPAA** (Saúde EUA) | ✅ Prontuários ficam locais |
| **Sigilo profissional** | ✅ Dados de clientes nunca saem do escritório |
| **Segredo industrial** | ✅ Só fictícios vão à nuvem |

---

## Fase 2 — Em andamento 🚀

### Conquistas
- ✅ Repositório GitHub publicado
- ✅ Release v1.0.0 publicada
- ✅ Landing page ao vivo em 6 idiomas (PT, EN, ES, ZH, HI, HE)
- ✅ Lista de espera integrada ao Google Sheets e testada
- ✅ Tabela dos 19 passos no README e na landing page
- ✅ `file_registry.py` — nome do arquivo protegido desde o passo 1
- ✅ **Amostragem inteligente v5.1** — `calculate_sample_size()` implementada

### Próximos passos
- [ ] Postar no LinkedIn (3 versões prontas)
- [ ] Configurar Google Analytics na landing page
- [ ] Prospectar primeiros clientes (advocacia prioritária)
- [ ] MVP SaaS com receita de consultoria

---

## Links importantes

| Recurso | URL |
|---|---|
| GitHub | github.com/myrkis-br/psa-privacy-shield-agent-for-ai |
| Site | myrkis-br.github.io/psa-privacy-shield-agent-for-ai |
| Release | github.com/myrkis-br/psa-privacy-shield-agent-for-ai/releases/tag/v1.0.0 |

---

## Conceito original
*PSA como opção nativa nas configurações de qualquer IA: "Modo PSA ativo — dados anonimizados antes do envio". Ideia original de Marcos Cruz, março 2026.*
