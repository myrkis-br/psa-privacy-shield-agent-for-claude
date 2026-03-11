"""
Gera o PDF PSA-Arquitetura-v6.0.pdf com o mesmo estilo visual do v5.1.
"""

from fpdf import FPDF
from pathlib import Path
import os

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "historico" / "PSA-Arquitetura-v6.0.pdf"


class PSAPdf(FPDF):
    """PDF estilizado para documentação PSA."""

    # Cores (RGB)
    DARK_BG = (30, 39, 50)       # fundo escuro (capa/rodapé)
    HEADER_BG = (70, 100, 120)   # azul-aço (títulos de seção)
    RED_ACCENT = (200, 60, 40)   # vermelho PSA
    GOLD = (210, 170, 50)        # dourado "CONFIDENCIAL"
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    LIGHT_GRAY = (245, 245, 245)
    MID_GRAY = (200, 200, 200)
    GREEN = (60, 140, 60)
    YELLOW_BG = (255, 245, 200)
    BLUE_CLOUD = (70, 100, 140)
    RED_BG = (220, 200, 200)
    GREEN_BG = (200, 230, 200)
    TEAL_HEADER = (90, 130, 140)  # tabela header

    FONT = "arialunicode"

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font(self.FONT, "", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
        self.add_font(self.FONT, "B", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
        self.add_font(self.FONT, "I", "/System/Library/Fonts/Supplemental/Arial Unicode.ttf")

    def _set_fill(self, rgb):
        self.set_fill_color(*rgb)

    def _set_text(self, rgb):
        self.set_text_color(*rgb)

    def _set_draw(self, rgb):
        self.set_draw_color(*rgb)

    # ── Capa ──────────────────────────────────────────────
    def cover_page(self):
        self.add_page()
        # Fundo escuro
        self._set_fill(self.DARK_BG)
        self.rect(0, 0, 210, 297, "F")

        # Logo PSA (blocos vermelhos)
        x0, y0 = 75, 30
        self._set_fill(self.RED_ACCENT)
        self.rect(x0, y0, 18, 22, "F")
        self.rect(x0 + 22, y0, 18, 22, "F")
        self.rect(x0 + 44, y0, 18, 22, "F")
        self.rect(x0 + 22, y0 + 4, 18, 18, "F")  # overlap central

        # "PSA" no logo
        self._set_text(self.WHITE)
        self.set_font("arialunicode", "B", 28)
        self.set_xy(x0 - 2, y0 + 3)
        self.cell(64, 20, "PSA", align="C")

        # Título principal
        self._set_text(self.WHITE)
        self.set_font("arialunicode", "B", 30)
        self.set_xy(10, 70)
        self.cell(190, 14, "Privacy Shield Agent for AI", align="C")

        # Subtítulo
        self.set_font("arialunicode", "", 14)
        self.set_xy(10, 95)
        self.cell(190, 8, "Documento de Arquitetura — v6.0", align="C")

        self.set_font("arialunicode", "", 12)
        self.set_xy(10, 110)
        self.cell(190, 8, "Risk Engine · 9 Formatos · RIPD Automático · 100/100", align="C")

        # Autor e data
        self.set_font("arialunicode", "", 10)
        self.set_xy(10, 135)
        self.cell(190, 7, "Marcos Cruz · Brasília/DF · Assistido por Claude (Anthropic)", align="C")
        self.set_xy(10, 145)
        self.cell(190, 7, "11 de Março de 2026", align="C")

        # CONFIDENCIAL
        self._set_text(self.GOLD)
        self.set_font("arialunicode", "B", 16)
        self.set_xy(10, 170)
        self.cell(190, 10, "CONFIDENCIAL", align="C")

        # Rodapé da capa
        self._set_text((180, 180, 180))
        self.set_font("arialunicode", "", 8)
        self.set_xy(10, 250)
        self.multi_cell(
            190, 5,
            "FASE 1 COMPLETA · Auditoria 100/100 · 28/28 vulnerabilidades corrigidas\n"
            "FASE 2 EM ANDAMENTO · Risk Engine v6.0 · 9 formatos validados · ZERO vazamentos",
            align="C",
        )

    # ── Seção header ──────────────────────────────────────
    def section_header(self, number, title):
        self.add_page()
        self._set_fill(self.HEADER_BG)
        self._set_text(self.WHITE)
        self.set_font("arialunicode", "B", 18)
        self.rect(10, 10, 190, 14, "F")
        self.set_xy(14, 10)
        self.cell(180, 14, f"{number}. {title}")
        self.ln(20)

    # ── Tabela genérica ───────────────────────────────────
    def styled_table(self, headers, rows, col_widths, header_bg=None, alt_rows=True):
        hbg = header_bg or self.TEAL_HEADER
        x_start = self.get_x()
        y_start = self.get_y()

        # Header
        self._set_fill(hbg)
        self._set_text(self.WHITE)
        self.set_font("arialunicode", "B", 9)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("arialunicode", "", 8)
        self._set_text(self.BLACK)
        for ri, row in enumerate(rows):
            if alt_rows and ri % 2 == 1:
                self._set_fill(self.LIGHT_GRAY)
                fill = True
            else:
                self._set_fill(self.WHITE)
                fill = True
            for i, val in enumerate(row):
                self.cell(col_widths[i], 7, str(val), border=1, fill=fill, align="C")
            self.ln()

    # ── Caixa de destaque ─────────────────────────────────
    def highlight_box(self, text, bg=None):
        bg = bg or self.LIGHT_GRAY
        self._set_fill(bg)
        self._set_text(self.BLACK)
        self.set_font("arialunicode", "", 10)
        x = self.get_x()
        y = self.get_y()
        self.rect(15, y, 180, 18, "F")
        self._set_draw(self.MID_GRAY)
        self.rect(15, y, 180, 18, "D")
        self.set_xy(18, y + 2)
        self.multi_cell(174, 5, text, align="C")
        self.set_y(y + 22)

    # ── Texto normal ──────────────────────────────────────
    def body_text(self, text, size=10, bold=False):
        self._set_text(self.BLACK)
        style = "B" if bold else ""
        self.set_font("arialunicode", style, size)
        self.multi_cell(180, 5, text)
        self.ln(2)

    # ── Rodapé ────────────────────────────────────────────
    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self._set_fill(self.DARK_BG)
        self.rect(0, self.get_y() - 2, 210, 16, "F")
        self._set_text((180, 180, 180))
        self.set_font("arialunicode", "", 7)
        self.cell(
            190, 8,
            f"PSA Privacy Shield Agent v6.0 · Risk Engine · 9 Formatos · 7.300+ linhas · "
            f"100/100 · Marcos Cruz · Março 2026  —  Pág. {self.page_no()}",
            align="C",
        )


def build():
    pdf = PSAPdf()

    # ══════════════════════════════════════════════════════
    # CAPA
    # ══════════════════════════════════════════════════════
    pdf.cover_page()

    # ══════════════════════════════════════════════════════
    # 1. SEGURANÇA EM PRIMEIRO LUGAR
    # ══════════════════════════════════════════════════════
    pdf.section_header(1, "Segurança em Primeiro Lugar")

    pdf.highlight_box(
        "A mensagem correta:\n"
        "PSA não é uma ferramenta de produtividade.\n"
        "É uma camada de segurança que, como consequência,\n"
        "também economiza 99% dos tokens e torna qualquer análise 30x mais rápida."
    )

    pdf.body_text("Os 4 Medos que o PSA Resolve", size=13, bold=True)
    pdf.styled_table(
        headers=["Medo", "Problema real", "Solução PSA"],
        rows=[
            ["Vazamento de clientes", "CPF, salário, endereço vão a servidores externos", "Dados reais nunca saem — só fictícios"],
            ["Multa LGPD/GDPR", "ANPD pode multar até 2% do faturamento anual", "Compliance automático + log auditável"],
            ["Segredo industrial", "Preços, margens e clientes VIP vão à nuvem", "Apenas dados fictícios chegam à nuvem"],
            ["Treinar concorrentes", "Dados podem alimentar modelos futuros da IA", "Nenhum dado real alimenta nenhum modelo"],
        ],
        col_widths=[40, 70, 80],
        header_bg=(140, 70, 70),
    )

    # ══════════════════════════════════════════════════════
    # 2. RISK ENGINE v6.0
    # ══════════════════════════════════════════════════════
    pdf.section_header(2, "Risk Engine v6.0 — NOVO")

    pdf.highlight_box(
        "O PSA agora classifica automaticamente o risco LGPD de cada documento (1-10),\n"
        "ajusta a cobertura e gera relatório RIPD — tudo 100% local, sem enviar dados."
    )

    pdf.body_text("Módulos do Risk Engine v6.0", size=12, bold=True)
    pdf.styled_table(
        headers=["Módulo", "Linhas", "Função"],
        rows=[
            ["classifier.py", "987", "Classifica risco LGPD 1-10 (Resolução ANPD nº 4/2023)"],
            ["pattern_enricher.py", "579", "Aprende padrões via cloud — ZERO dado real transmitido"],
            ["ripd_report.py", "574", "Relatório RIPD automático (Art. 38 LGPD)"],
            ["psa.py (integrado)", "1.138", "Orquestrador: modo ECO/PADRÃO/MÁXIMO por risco"],
        ],
        col_widths=[40, 20, 130],
    )

    pdf.ln(4)
    pdf.body_text("Classificação automática de risco LGPD:", size=10, bold=True)
    pdf.styled_table(
        headers=["Score", "Nível", "Cobertura", "Ação"],
        rows=[
            ["1-3", "LEVE", "30%", "Amostragem mínima"],
            ["4-6", "MÉDIA", "60%", "Amostragem padrão"],
            ["7-10", "GRAVE", "100%", "Cobertura total obrigatória"],
        ],
        col_widths=[25, 30, 35, 100],
    )

    pdf.ln(4)
    pdf.body_text("Seleção de modo (quando custo estimado >= R$ 0,10):", size=10, bold=True)
    pdf.styled_table(
        headers=["Modo", "Cobertura", "Quando usar"],
        rows=[
            ["ECO", "30%", "Exploração rápida, análise preliminar"],
            ["PADRÃO", "60%", "Uso normal, boa cobertura"],
            ["MÁXIMO", "100%", "Risco GRAVE, compliance total"],
        ],
        col_widths=[30, 30, 130],
    )

    # ══════════════════════════════════════════════════════
    # 3. AMOSTRAGEM INTELIGENTE v5.1
    # ══════════════════════════════════════════════════════
    pdf.section_header(3, "Amostragem Inteligente — v5.1")

    pdf.highlight_box(
        "O PSA é estatisticamente inteligente — envia o mínimo necessário\n"
        "para cada tamanho de arquivo, nunca mais do que precisa."
    )

    pdf.body_text(
        "A função calculate_sample_size(n_rows) determina automaticamente "
        "o tamanho ideal da amostra, baseada no Teorema Central do Limite "
        "(mínimo estatisticamente válido: 30 observações).", size=9
    )

    pdf.styled_table(
        headers=["Tamanho do arquivo", "Amostra enviada", "Lógica", "% enviado (ex: 256k)"],
        rows=[
            ["<= 30 linhas", "100% (tudo)", "Arquivo pequeno — aviso no log", "100%"],
            ["31 a 100", "50% (mín. 30)", "Mantém representatividade", "50%"],
            ["101 a 10.000", "100 linhas", "Padrão — mínimo válido", "1% a 0,01%"],
            ["10.001 a 100.000", "150 linhas", "Arquivo grande", "0,01% a 0,001%"],
            ["100.001+", "200 linhas", "Máximo recomendado", "0,001% ou menos"],
        ],
        col_widths=[35, 35, 65, 55],
    )

    pdf.ln(4)
    pdf.body_text("Regras de segurança da amostragem:", size=10, bold=True)
    pdf.body_text(
        "• A amostra nunca pode ser maior que o arquivo real\n"
        "• --sample N sobrescreve a lógica automática\n"
        "• Log registra: tamanho real, amostra e % enviado\n"
        "• Base: Teorema Central do Limite — 30 amostras garantem representatividade\n"
        "• Arquivo <= 30 linhas gera aviso explícito no log",
        size=9,
    )

    # ══════════════════════════════════════════════════════
    # 4. OS 19 PASSOS (REVISADOS v6.0)
    # ══════════════════════════════════════════════════════
    pdf.section_header(4, "Como o PSA Protege — Os 19 Passos (v6.0)")

    pdf.highlight_box(
        "16 de 19 passos rodam 100% local. Seus dados reais jamais saem do seu computador.\n"
        "Consequência: economia de até 99,96% dos tokens · Análises de 15 min em 30 segundos"
    )

    pdf.styled_table(
        headers=["Passo", "O que acontece", "Local/Nuvem", "Token?", "Dados saem?"],
        rows=[
            ["1", "Nome → código genérico (DOC_001) via file_registry", "Local", "Não", "Nem o nome sai"],
            ["2", "PSA invoca psa.py via código genérico", "Local", "Não", "Não"],
            ["3", "Valida segurança do arquivo", "Local", "Não", "Não"],
            ["4", "Detecta extensão e escolhe script (9 formatos)", "Local", "Não", "Não"],
            ["4b", "RISK ENGINE: classifica risco LGPD 1-10 [v6.0]", "Local", "Não", "Não"],
            ["4c", "Seleciona modo ECO/PADRÃO/MÁXIMO [v6.0]", "Local", "Não", "Não"],
            ["5", "Lê o arquivo real do disco", "Local", "Não", "Não"],
            ["6", "Amostragem inteligente — ajustada por risk_score", "Local", "Não", "Não"],
            ["7", "Detecta campos sensíveis (70+ keywords + tags)", "Local", "Não", "Não"],
            ["8", "Renomeia colunas para COL_A, COL_B...", "Local", "Não", "Não"],
            ["9", "Anonimiza com Faker pt_BR offline", "Local", "Não", "Não"],
            ["10", "Varia valores financeiros em ±15%", "Local", "Não", "Não"],
            ["11", "Escaneia textos livres e substitui (regex)", "Local", "Não", "Não"],
            ["12", "Anti-vazamento: detectou dado real → DELETA", "Local", "Não", "Não"],
            ["13", "Salva anonimizado em data/anonymized/", "Local", "Não", "Não"],
            ["14", "Salva mapa em data/maps/", "Local", "Não", "Não"],
            ["15", "Gera RIPD automático (Art. 38 LGPD) [v6.0]", "Local", "Não", "Não"],
            ["16", "IA lê o arquivo anonimizado", "Nuvem", "Sim", "Só fictícios"],
            ["17", "IA realiza análise e responde", "Nuvem", "Sim", "Só fictícios"],
            ["18", "IA gera script Python para rodar localmente", "Nuvem", "Sim", "Só código"],
            ["19", "Script roda nos dados reais → results/", "Local", "Não", "Não"],
        ],
        col_widths=[12, 80, 28, 18, 52],
    )

    pdf.ln(3)
    pdf._set_text(pdf.BLACK)
    pdf.set_font("arialunicode", "I", 8)
    pdf.cell(190, 5, "Verde = local. Laranja = novo v6.0. Azul = nuvem (apenas dados fictícios ou código).", align="C")

    # ══════════════════════════════════════════════════════
    # 5. CONFORMIDADE
    # ══════════════════════════════════════════════════════
    pdf.section_header(5, "Conformidade Garantida")

    pdf.styled_table(
        headers=["Regulação", "Exigência", "PSA"],
        rows=[
            ["LGPD (Brasil)", "Dados pessoais não saem sem consentimento", "Anonimização antes do envio"],
            ["GDPR (Europa)", "Dados de cidadãos europeus protegidos", "Apenas fictícios chegam à nuvem"],
            ["HIPAA (Saúde EUA)", "Dados de pacientes não transitam sem proteção", "Prontuários ficam locais"],
            ["Sigilo profissional", "Advogados/médicos têm dever legal de sigilo", "Dados do cliente nunca saem"],
            ["Segredo industrial", "Dados estratégicos protegidos por NDA", "Só fictícios vão à nuvem"],
            ["Auditoria", "Empresas precisam provar que não vazaram dados", "Log auditável + RIPD automático"],
        ],
        col_widths=[35, 80, 75],
        header_bg=(140, 70, 70),
    )

    pdf.ln(6)
    pdf.highlight_box(
        "Validação real: base GDF com 256.013 servidores públicos\n"
        "Nomes vazados: ZERO · CPFs vazados: ZERO · Auditoria: 100/100"
    )

    # ══════════════════════════════════════════════════════
    # 6. PLACAR DE TESTES v6.0
    # ══════════════════════════════════════════════════════
    pdf.section_header(6, "Placar de Testes — v6.0 Risk Engine")

    pdf.highlight_box(
        "9 formatos validados · 5 documentos testados · 489 entidades anonimizadas\n"
        "ZERO vazamentos em todos os testes · Relatório RIPD automático em cada execução"
    )

    pdf.body_text("Resultados detalhados por documento:", size=11, bold=True)
    pdf.styled_table(
        headers=["DOC", "Tipo", "Formato", "Score", "Entidades", "Vazamentos", "Multa evitada"],
        rows=[
            ["DOC_016", "RH (50 func.)", "CSV", "7/10 GRAVE", "15", "ZERO", "R$ 500k-5M"],
            ["DOC_017", "BACEN (4.560 serv.)", "CSV", "5/10 MÉDIA", "3", "ZERO", "R$ 50k-500k"],
            ["DOC_019", "Laudo médico", "DOCX", "9/10 GRAVE", "85", "ZERO", "R$ 500k-5M"],
            ["DOC_020", "API payments", "JSON", "7/10 GRAVE", "358", "ZERO", "R$ 500k-5M"],
            ["DOC_021", "NF-e fiscal", "XML", "6/10 MÉDIA", "28", "ZERO", "R$ 50k-500k"],
        ],
        col_widths=[18, 38, 16, 28, 22, 22, 46],
    )

    pdf.ln(5)
    pdf.body_text("Formatos validados:", size=11, bold=True)
    pdf.styled_table(
        headers=["Formato", "Script", "Linhas", "Destaques"],
        rows=[
            ["CSV/XLSX", "anonymizer.py", "961", "70+ keywords, amostragem inteligente"],
            ["PDF", "anonymize_pdf.py", "329", "pdfplumber, amostragem por páginas"],
            ["DOCX/TXT", "anonymize_document.py", "347", "Headers/footers, encoding fallback"],
            ["PPTX", "anonymize_presentation.py", "375", "JSON estruturado por slide"],
            ["EML/MSG", "anonymize_email.py", "442", "Campos + corpo, warning anexos"],
            ["JSON", "anonymize_json.py", "488", "Travessia recursiva, detecção por chave"],
            ["XML", "anonymize_xml.py", "386", "Namespaces SEFAZ, 14 tags sensíveis"],
        ],
        col_widths=[24, 48, 18, 100],
    )

    # ══════════════════════════════════════════════════════
    # 7. ECONOMIA DE TOKENS
    # ══════════════════════════════════════════════════════
    pdf.section_header(7, "Economia de Tokens e Tempo — Consequência da Segurança")

    pdf.highlight_box(
        "A economia é consequência da proteção, não o produto principal.\n"
        "Para não enviar dados reais, o PSA usa amostragem inteligente\n"
        "— e isso reduz tokens em até 99,96%."
    )

    pdf.styled_table(
        headers=["Segmento", "Linhas Reais", "Amostra PSA", "Economia Tokens", "Tempo SEM PSA", "Tempo COM PSA"],
        rows=[
            ["Governo/GDF", "256.000", "200 linhas", "99,92%", "~18 min", "~30s"],
            ["Finanças", "50.000", "150 linhas", "99,7%", "~9 min", "~30s"],
            ["Saúde", "10.000", "100 linhas", "99%", "~7 min", "~30s"],
            ["Advocacia", "5.000", "100 linhas", "98%", "~4 min", "~30s"],
            ["RH/Contabil.", "500", "100 linhas", "80%", "~1 min", "~30s"],
            ["PME", "25", "25 (tudo)", "0%", "~10s", "~15s"],
        ],
        col_widths=[30, 26, 28, 30, 28, 28],
    )

    # ══════════════════════════════════════════════════════
    # 8. INVENTÁRIO DO PROJETO
    # ══════════════════════════════════════════════════════
    pdf.section_header(8, "Inventário do Projeto")

    pdf.highlight_box(
        "7.300+ linhas Python · 13 scripts core · 3 agentes · 9 formatos · 70+ keywords"
    )

    pdf.body_text("Scripts Principais", size=12, bold=True)
    pdf.styled_table(
        headers=["Script", "Linhas", "Função"],
        rows=[
            ["psa.py", "1.138", "Interface unificada + Risk Engine + modo ECO/PADRÃO/MÁXIMO"],
            ["anonymizer.py", "961", "Planilhas CSV/XLSX. calculate_sample_size(). 70+ keywords."],
            ["classifier.py", "987", "Classifica risco LGPD 1-10. JSON/XML/CSV/DOCX/PDF."],
            ["pattern_enricher.py", "579", "Aprende padrões via cloud. ZERO dado real transmitido."],
            ["ripd_report.py", "574", "Relatório RIPD automático (Art. 38 LGPD)."],
            ["file_registry.py", "287", "Protege nomes desde o passo 1 (DOC_NNN)."],
            ["text_engine.py", "426", "Motor de regex. ALL-CAPS, honoríficos, endereços."],
            ["anonymize_json.py", "488", "JSON recursivo. Detecção por chave + contexto."],
            ["anonymize_xml.py", "386", "XML/NF-e. Namespaces SEFAZ. 14 tags + text_engine."],
            ["anonymize_document.py", "347", "DOCX/TXT. Headers/footers. Encoding fallback."],
            ["anonymize_pdf.py", "329", "PDF via pdfplumber. Amostragem por páginas."],
            ["anonymize_presentation.py", "375", "PPTX → JSON estruturado por slide."],
            ["anonymize_email.py", "442", "EML/MSG. Campos + corpo. Warning para anexos."],
        ],
        col_widths=[42, 16, 132],
    )

    # ══════════════════════════════════════════════════════
    # 9. ROADMAP
    # ══════════════════════════════════════════════════════
    pdf.section_header(9, "Roadmap")

    pdf.body_text("Fase 1 — COMPLETA", size=13, bold=True)
    pdf.body_text(
        "• 3 agentes + 8 scripts (12 total, 5.068+ linhas) · 11 formatos · 70+ keywords\n"
        "• Auditoria 100/100 · 28/28 vulnerabilidades corrigidas\n"
        "• Teste real: 256k linhas GDF — zero vazamentos\n"
        "• file_registry.py: nome do arquivo protegido desde o passo 1\n"
        "• Amostragem inteligente v5.1: calculate_sample_size()",
        size=9,
    )

    pdf.body_text("Fase 2 — Em andamento (Risk Engine v6.0)", size=13, bold=True)
    pdf.body_text(
        "• GitHub público + landing page ao vivo · 6 idiomas\n"
        "• Lista de espera integrada e testada\n"
        "• Risk Engine v6.0: classifier + enricher + RIPD automático\n"
        "• JSON + XML/NF-e: 2 novos formatos (total: 9 validados)\n"
        "• 7.300+ linhas Python em 13 scripts core\n"
        "• 5 DOCs testados: 489 entidades, ZERO vazamentos\n"
        "• Seleção de modo ECO/PADRÃO/MÁXIMO por nível de risco",
        size=9,
    )

    pdf.body_text("Fase 3 — Escala", size=13, bold=True)
    pdf.body_text(
        "• Publicar como skill open-source no GitHub\n"
        "• Proposta formal à Anthropic para integração nativa\n"
        "• Consultoria especializada em privacidade + IA\n"
        "• Upgrade hardware (Mac Mini M4 Pro 48 GB)",
        size=9,
    )

    # ══════════════════════════════════════════════════════
    # 10. GLOSSÁRIO
    # ══════════════════════════════════════════════════════
    pdf.section_header(10, "Glossário")

    pdf.styled_table(
        headers=["Termo", "Significado"],
        rows=[
            ["PSA", "Privacy Shield Agent — camada de segurança para uso de IA"],
            ["Risk Engine", "Módulo v6.0 — classifica risco LGPD 1-10 automaticamente"],
            ["RIPD", "Relatório de Impacto à Proteção de Dados (Art. 38 LGPD)"],
            ["classifier.py", "Classifica risco: tipo, subtipo, titulares, categorias sensíveis"],
            ["calculate_sample_size", "Função v5.1 — calcula amostra mínima por faixa de tamanho"],
            ["file_registry", "Módulo que substitui nomes reais por códigos DOC_NNN"],
            ["DOC_NNN", "Código genérico para nome de arquivo (ex: DOC_001.xlsx)"],
            ["Amostragem inteligente", "Envio do mínimo estatisticamente válido"],
            ["Anonimização", "Substituição de dados reais por fictícios (Faker pt_BR)"],
            ["LeakageError", "Exceção lançada quando dado real detectado — deleta e bloqueia"],
            ["text_engine", "Motor de regex do PSA (70+ patterns)"],
            ["Mapa", "Arquivo local real→fake em data/maps/ (nunca sai do Mac)"],
            ["LGPD", "Lei Geral de Proteção de Dados — Brasil"],
            ["GDPR", "General Data Protection Regulation — Europa"],
            ["TCL", "Teorema Central do Limite — base da amostragem (n>=30)"],
            ["NF-e", "Nota Fiscal Eletrônica — XML com namespace SEFAZ"],
        ],
        col_widths=[42, 148],
    )

    # ── Salva ─────────────────────────────────────────────
    pdf.output(str(OUTPUT))
    print(f"PDF gerado: {OUTPUT}")
    print(f"Tamanho: {OUTPUT.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
