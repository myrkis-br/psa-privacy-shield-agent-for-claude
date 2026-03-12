#!/usr/bin/env python3
"""
Gera o documento de arquitetura PSA v6.1 em PDF.
Usa reportlab para criar um PDF profissional com Helvetica.
"""

import os
import sys

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable
    )
except ImportError:
    print("reportlab nao encontrado. Instalando...")
    os.system("pip3 install reportlab")
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.colors import HexColor, white, black
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable
    )


# -- Cores -----------------------------------------------------------------
BLUE_DARK = HexColor("#1a365d")
BLUE_MID = HexColor("#2b6cb0")
BLUE_LIGHT = HexColor("#ebf4ff")
BLUE_ACCENT = HexColor("#3182ce")
GRAY_LIGHT = HexColor("#f7fafc")
GRAY_MID = HexColor("#e2e8f0")
GRAY_TEXT = HexColor("#4a5568")

# -- Caminhos --------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "docs", "historico")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "PSA-Arquitetura-v6.1.pdf")


def build_styles():
    """Cria estilos customizados com Helvetica."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=28,
        textColor=BLUE_DARK,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        textColor=BLUE_MID,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="DocAuthor",
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=GRAY_TEXT,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))

    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=22,
        textColor=BLUE_DARK,
        spaceBefore=18,
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name="BodyText2",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=black,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="BulletPSA",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=black,
        leftIndent=20,
        spaceAfter=4,
        bulletIndent=8,
    ))

    styles.add(ParagraphStyle(
        name="SmallNote",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=GRAY_TEXT,
        alignment=TA_CENTER,
        spaceAfter=4,
    ))

    return styles


def section_header(text, styles):
    """Cria header de secao com linha azul embaixo."""
    return [
        Paragraph(text, styles["SectionHeader"]),
        HRFlowable(width="100%", thickness=2, color=BLUE_ACCENT,
                    spaceAfter=8, spaceBefore=0),
    ]


def bullet(text, styles):
    """Cria bullet point."""
    return Paragraph(
        "<bullet>&bull;</bullet> " + text,
        styles["BulletPSA"]
    )


def make_table(header, rows, col_widths=None):
    """Cria tabela estilizada com header azul e linhas alternadas."""
    data = [header] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), BLUE_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, GRAY_MID),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, BLUE_ACCENT),
    ]
    # Alternate row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), BLUE_LIGHT))
        else:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), white))
    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf():
    """Gera o PDF completo."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="PSA - Privacy Shield Agent for AI - Arquitetura v6.1",
        author="Marcos Cruz",
    )

    styles = build_styles()
    story = []

    # -- Capa --------------------------------------------------------------
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(
        "PSA — Privacy Shield Agent for AI",
        styles["DocTitle"]
    ))
    story.append(Paragraph(
        "Arquitetura v6.1",
        styles["DocTitle"]
    ))
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="60%", thickness=2, color=BLUE_ACCENT,
                             spaceAfter=12, spaceBefore=0, hAlign="CENTER"))
    story.append(Paragraph(
        "Security Hardening + 21 Extensões",
        styles["DocSubtitle"]
    ))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "Marcos Cruz — Brasília/DF — 12/03/2026",
        styles["DocAuthor"]
    ))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(
        "Documento confidencial — uso interno",
        styles["SmallNote"]
    ))

    story.append(PageBreak())

    # -- 1. Visão Geral ----------------------------------------------------
    story.extend(section_header("1. Visão Geral", styles))
    story.append(Paragraph(
        "O PSA (Privacy Shield Agent) é uma camada de segurança local que "
        "intercepta e anonimiza dados sensíveis antes de enviá-los a qualquer "
        "inteligência artificial. O sistema garante que nenhum dado pessoal "
        "identificável (PII) saia do computador do usuário.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 4))
    story.append(bullet(
        "Compatível com <b>Claude, ChatGPT, Gemini, Llama</b> e qualquer API de IA",
        styles
    ))
    story.append(bullet(
        "100% local — dados reais jamais saem do computador",
        styles
    ))
    story.append(bullet(
        "v6.1: <b>21 extensões / 18 formatos únicos</b>, score de segurança <b>82/100</b>",
        styles
    ))
    story.append(bullet(
        "Compliance com LGPD (Art. 38 — RIPD automático)",
        styles
    ))
    story.append(bullet(
        "5 CVEs corrigidos nesta versão",
        styles
    ))

    story.append(Spacer(1, 12))

    # -- 2. Placar de Formatos ---------------------------------------------
    story.extend(section_header(
        "2. Placar de Formatos (21 extensões / 18 formatos)", styles
    ))
    story.append(Paragraph(
        "A tabela abaixo lista todos os formatos suportados pelo PSA v6.1, "
        "incluindo as extensões associadas e o script responsável pela anonimização.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 6))

    fmt_header = ["#", "Formato", "Extensões", "Script"]
    fmt_rows = [
        ["1",  "Planilha CSV",       ".csv",           "anonymizer.py"],
        ["2",  "Planilha Excel",     ".xlsx .xls",     "anonymizer.py"],
        ["3",  "Documento Word",     ".docx",          "anonymize_document.py"],
        ["4",  "Texto puro",         ".txt",           "anonymize_document.py"],
        ["5",  "PDF",                ".pdf",           "anonymize_pdf.py"],
        ["6",  "Apresentação",       ".pptx",          "anonymize_presentation.py"],
        ["7",  "E-mail EML",         ".eml",           "anonymize_email.py"],
        ["8",  "E-mail MSG",         ".msg",           "anonymize_email.py"],
        ["9",  "JSON",               ".json",          "anonymize_json.py"],
        ["10", "XML / NF-e",         ".xml",           "anonymize_xml.py"],
        ["11", "RTF",                ".rtf",           "anonymize_rtf.py"],
        ["12", "ODT",                ".odt",           "anonymize_odt.py"],
        ["13", "HTML",               ".html",          "anonymize_html.py"],
        ["14", "YAML",               ".yaml .yml",     "anonymize_yaml.py"],
        ["15", "SQL",                ".sql",           "anonymize_sql.py"],
        ["16", "Log",                ".log",           "anonymize_log.py"],
        ["17", "vCard",              ".vcf",           "anonymize_vcf.py"],
        ["18", "Parquet",            ".parquet",       "anonymize_parquet.py"],
    ]
    story.append(make_table(
        fmt_header, fmt_rows,
        col_widths=[1.2 * cm, 4.5 * cm, 3.5 * cm, 5.5 * cm]
    ))

    story.append(Spacer(1, 12))

    # -- 3. Segurança ------------------------------------------------------
    story.extend(section_header("3. Segurança — Score 82/100", styles))
    story.append(Paragraph(
        "O PSA v6.1 implementa 7 áreas de segurança auditadas, com 5 CVEs "
        "corrigidos nesta versão. O score atual é <b>82/100</b>.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 6))

    sec_header = ["Área", "Status", "Detalhe"]
    sec_rows = [
        ["Integridade de dados",  "✓",  "SHA-256 em cada arquivo processado"],
        ["Audit trail",           "✓",  "audit_trail.jsonl append-only"],
        ["Controle de mapas",     "✓",  "--no-map + --purge-maps"],
        ["Anti-vazamento",        "✓",  "Validação pós-anonimização + deleção automática"],
        ["Anti-injection",        "✓",  "Validação de nomes de arquivo"],
        ["Encoding",              "✓",  "Auto-detecção multi-encoding (UTF-8, Latin-1, CP1252)"],
        ["RIPD automático",       "✓",  "Art. 38 LGPD — relatório gerado automaticamente"],
    ]
    story.append(make_table(
        sec_header, sec_rows,
        col_widths=[4 * cm, 1.8 * cm, 9 * cm]
    ))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<b>5 CVEs corrigidos na v6.1:</b> path traversal, injection em nomes de arquivo, "
        "vazamento em logs, encoding bypass e race condition em mapas.",
        styles["BodyText2"]
    ))

    story.append(Spacer(1, 12))

    # -- 4. Fluxo de Dados -------------------------------------------------
    story.extend(section_header("4. Fluxo de Dados (19 Passos)", styles))
    story.append(Paragraph(
        "O fluxo completo do PSA compreende 19 passos, dos quais <b>16 rodam "
        "100% local</b> no computador do usuário. Apenas 3 passos envolvem "
        "comunicação com a nuvem, e nesses casos somente dados fictícios são transmitidos.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 6))
    story.append(bullet(
        "<b>16 de 19 passos</b> rodam 100% local — sem nenhum dado real exposto",
        styles
    ))
    story.append(bullet(
        "<b>Dados reais jamais saem do computador</b> — ficam em <i>data/real/</i>",
        styles
    ))
    story.append(bullet(
        "<b>3 passos em nuvem:</b> enviam apenas dados fictícios gerados pelo Faker",
        styles
    ))
    story.append(bullet(
        "Mapas de correspondência (real → fake) ficam em <i>data/maps/</i> — protegidos",
        styles
    ))
    story.append(bullet(
        "Audit trail registra cada operação em <i>audit_trail.jsonl</i>",
        styles
    ))

    story.append(Spacer(1, 8))

    flow_header = ["Etapa", "Local/Nuvem", "Descrição"]
    flow_rows = [
        ["1-3",   "Local",  "Usuário fornece arquivo → registro (DOC_NNN) → validação"],
        ["4-6",   "Local",  "Detecção de formato → seleção de script → leitura do arquivo"],
        ["7-9",   "Local",  "Detecção de colunas sensíveis → classificação LGPD → amostragem"],
        ["10-12", "Local",  "Geração de dados fictícios (Faker) → substituição → text_engine"],
        ["13-14", "Local",  "Validação anti-vazamento → SHA-256 → salvamento"],
        ["15",    "Local",  "Geração de mapa de correspondência (protegido)"],
        ["16",    "Local",  "Audit trail → RIPD automático"],
        ["17-19", "Nuvem",  "Envio de dados fictícios → análise pela IA → resposta ao usuário"],
    ]
    story.append(make_table(
        flow_header, flow_rows,
        col_widths=[2 * cm, 2.5 * cm, 10.2 * cm]
    ))

    story.append(PageBreak())

    # -- 5. Risk Engine ----------------------------------------------------
    story.extend(section_header("5. Risk Engine v6.0", styles))
    story.append(Paragraph(
        "O Risk Engine classifica automaticamente cada campo de dados conforme "
        "a LGPD, atribuindo um score de risco de 1 a 10. Com base nesse score, "
        "o PSA decide o nível de anonimização aplicado.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 6))
    story.append(bullet(
        "<b>Classificação automática LGPD</b> — score de risco 1 a 10 por campo",
        styles
    ))
    story.append(bullet(
        "<b>3 modos de operação:</b> ECO (mínimo), PADRÃO (recomendado), MÁXIMO (paranóico)",
        styles
    ))
    story.append(bullet(
        "<b>RIPD automático</b> — Relatório de Impacto à Proteção de Dados (Art. 38 LGPD)",
        styles
    ))

    story.append(Spacer(1, 8))

    risk_header = ["Modo", "Score mín.", "Comportamento"]
    risk_rows = [
        ["ECO",     "1-3",   "Anonimiza apenas campos de alto risco; máxima performance"],
        ["PADRÃO",  "4-7",   "Anonimiza campos sensíveis + text_engine em texto livre"],
        ["MÁXIMO",  "8-10",  "Anonimiza tudo; inclui ofuscação de estrutura e metadados"],
    ]
    story.append(make_table(
        risk_header, risk_rows,
        col_widths=[2.5 * cm, 2.5 * cm, 9.7 * cm]
    ))

    story.append(Spacer(1, 18))

    # -- 6. Roadmap --------------------------------------------------------
    story.extend(section_header("6. Roadmap", styles))
    story.append(Paragraph(
        "Próximos passos planejados para o PSA, visando expandir a compatibilidade "
        "e alcançar os primeiros usuários reais.",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 6))

    road_header = ["Prioridade", "Item", "Status"]
    road_rows = [
        ["1", "GPT Store (ChatGPT) — publicação como plugin",    "Próximo passo"],
        ["2", "Gemini Workspace — integração corporativa",        "Fase seguinte"],
        ["3", "LinkedIn marketing — divulgação e posicionamento", "Planejado"],
        ["4", "Piloto com cliente real — validação em produção",  "Planejado"],
    ]
    story.append(make_table(
        road_header, road_rows,
        col_widths=[2.2 * cm, 8.5 * cm, 4 * cm]
    ))

    story.append(Spacer(1, 2 * cm))

    # -- Rodapé ------------------------------------------------------------
    story.append(HRFlowable(width="100%", thickness=1, color=GRAY_MID,
                             spaceAfter=8, spaceBefore=0))
    story.append(Paragraph(
        "PSA — Privacy Shield Agent for AI — v6.1 — Marcos Cruz — Brasília/DF — 12/03/2026",
        styles["SmallNote"]
    ))
    story.append(Paragraph(
        "Documento gerado automaticamente. Distribuição restrita.",
        styles["SmallNote"]
    ))

    # -- Build -------------------------------------------------------------
    doc.build(story)
    print(f"PDF gerado com sucesso: {OUTPUT_FILE}")
    print(f"Tamanho: {os.path.getsize(OUTPUT_FILE):,} bytes")


if __name__ == "__main__":
    build_pdf()
