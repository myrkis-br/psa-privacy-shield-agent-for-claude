"""
PSA - Análise gerada pelo CFO
Pedido : Auditoria completa da folha de pagamento do GDF — Junho/2025
Entrada: data/real/remuneracao202506.csv (256.013 linhas)
Saída  : results/analise_remuneracao_gdf.html
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "real" / "remuneracao202506.csv"
OUT_DIR   = BASE_DIR / "results"
OUT_DIR.mkdir(exist_ok=True)
OUT_HTML  = OUT_DIR / "analise_remuneracao_gdf.html"

# ──────────────────────────────────────────────────────────────────────────
# CONSTANTES LEGAIS
# ──────────────────────────────────────────────────────────────────────────
# Teto constitucional: subsídio dos Ministros do STF (Art. 37, XI, CF/88)
TETO_STF = 46_366.19  # 2025 — atualize se houver reajuste

# Situações ATIVAS para fins do limite de cargos (Art. 37, XVI, CF/88)
# Aposentadoria, Pensão e Demissão NÃO contam para o limite
SITUACOES_ATIVAS = {
    "ATIVO", "ATIVO PERMANENTE", "TRABALHANDO",
    "COMISSIONADO", "CEDIDO", "CONSELHEIRO",
}

# ──────────────────────────────────────────────────────────────────────────
# 1. CARGA E LIMPEZA
# ──────────────────────────────────────────────────────────────────────────
print("Carregando dados reais...")
df = pd.read_csv(DATA_PATH, dtype=str, encoding="latin-1", sep=";")

def parse_br(series):
    return (series.str.strip()
                  .str.replace(r"\.", "", regex=True)
                  .str.replace(",", ".", regex=False)
                  .replace("", np.nan).astype(float).fillna(0.0))

for col in ["BRUTO","LÍQUIDO","REMUNERAÇÃO BÁSICA"]:
    df[col + "_N"] = parse_br(df[col])

df["ÓRGÃO"]    = df["ÓRGÃO"].str.strip()
df["CARGO"]    = df["CARGO"].str.strip()
df["SITUAÇÃO"] = df["SITUAÇÃO"].str.strip().str.upper()
df["CPF"]      = df["CPF"].str.strip()
df["NOME"]     = df["NOME"].str.strip()

# --- Ativo vs inativo ---
_afastado     = df["SITUAÇÃO"].str.startswith("AFASTADO").fillna(False)
df["IS_ATIVO"] = df["SITUAÇÃO"].isin(SITUACOES_ATIVAS) | _afastado

# --- Tipo de vínculo (para classificação legal) ---
# CONSELHO : mandato societário — NÃO conta para o limite de 2 cargos
# COMISSIONADO : função/cargo comissionado — 1 por pessoa máximo
# EFETIVO : cargo efetivo/emprego — conta para limite
# INATIVO : aposentado, pensionista, demitido
df["TIPO_VINC"] = "INATIVO"
_is_ativo = df["IS_ATIVO"]
df.loc[_is_ativo & (df["SITUAÇÃO"] == "CONSELHEIRO"),  "TIPO_VINC"] = "CONSELHO"
df.loc[_is_ativo & (df["SITUAÇÃO"] == "COMISSIONADO"), "TIPO_VINC"] = "COMISSIONADO"
df.loc[_is_ativo & ~df["SITUAÇÃO"].isin({"CONSELHEIRO","COMISSIONADO"}), "TIPO_VINC"] = "EFETIVO"

df["ACIMA_TETO"] = df["BRUTO_N"] > TETO_STF

total_serv    = len(df)
folha_total   = df["BRUTO_N"].sum()
media_geral   = df["BRUTO_N"].mean()
mediana_geral = df["BRUTO_N"].median()
print(f"Base: {total_serv:,} servidores | Folha: R$ {folha_total:,.2f}")

df_at = df[df["IS_ATIVO"]].copy()
print(f"Ativos: {len(df_at):,} | Inativos: {len(df)-len(df_at):,}")

# ──────────────────────────────────────────────────────────────────────────
# 2. ANÁLISE 1 — OUTLIERS SALARIAIS (apenas ATIVOS)
# ──────────────────────────────────────────────────────────────────────────
print("Calculando outliers (ativos)...")
stats_cargo = (df_at.groupby("CARGO")["BRUTO_N"]
                 .agg(n="count", media="mean", std="std").reset_index())
stats_cargo = stats_cargo[stats_cargo["n"] >= 15].copy()
stats_cargo["lim_sup"] = stats_cargo["media"] + 2 * stats_cargo["std"]

df_out   = df_at.merge(stats_cargo[["CARGO","media","std","lim_sup","n"]], on="CARGO")
outliers = df_out[df_out["BRUTO_N"] > df_out["lim_sup"]].copy()
outliers["desvios"] = ((outliers["BRUTO_N"] - outliers["media"]) / outliers["std"]).round(1)
outliers  = outliers.sort_values("desvios", ascending=False)
n_outliers = len(outliers)

_oo = (outliers.groupby("ÓRGÃO")["NOME"].count()
               .sort_values(ascending=False).head(12).reset_index())
_oo.columns = ["orgao","n"]
_oo["orgao"] = _oo["orgao"].str[:45]
j_out_orgao_labels = json.dumps(_oo["orgao"].tolist())
j_out_orgao_data   = json.dumps(_oo["n"].tolist())

def rows_outliers(df_):
    rows = []
    for _, r in df_.head(30).iterrows():
        sev   = "🔴" if r["desvios"] > 4 else ("🟠" if r["desvios"] > 3 else "🟡")
        teto_f = " <span style='color:#ef4444;font-size:10px'>⚠TETO</span>" if r["ACIMA_TETO"] else ""
        rows.append(
            f'<tr><td>{sev} {r["desvios"]:.1f}σ</td>'
            f'<td>{r["NOME"]}</td>'
            f'<td>{str(r["CARGO"])[:42]}</td>'
            f'<td>{str(r["ÓRGÃO"])[:50]}</td>'
            f'<td class="num">{brl(r["BRUTO_N"])}{teto_f}</td>'
            f'<td class="num muted">{brl(r["media"])}</td>'
            f'<td class="num muted">{r["desvios"]:.1f}x</td></tr>'
        )
    return "\n".join(rows)

# ──────────────────────────────────────────────────────────────────────────
# 3. ANÁLISE 2 — DISPARIDADE POR CARGO (apenas ATIVOS)
# Aposentados excluídos: podem ter pagamentos acumulados (retroativos,
# 13º, precatórios) que distorceriam a análise de remuneração corrente.
# ──────────────────────────────────────────────────────────────────────────
print("Calculando disparidade (ativos)...")
disp = (df_at[df_at["BRUTO_N"] > 0].groupby("CARGO")["BRUTO_N"]
          .agg(n="count", media="mean", minimo="min", maximo="max", std="std")
          .reset_index())
disp = disp[disp["n"] >= 20].copy()
disp["amplitude"]  = disp["maximo"] - disp["minimo"]
disp["cv"]         = (disp["std"] / disp["media"] * 100).round(1)
disp["acima_teto"] = disp["maximo"] > TETO_STF
disp = disp.sort_values("amplitude", ascending=False)

_d15 = disp.head(15)
j_disp_labels = json.dumps(_d15["CARGO"].str[:40].tolist())
j_disp_min    = json.dumps(_d15["minimo"].round(2).tolist())
j_disp_media  = json.dumps(_d15["media"].round(2).tolist())
j_disp_max    = json.dumps(_d15["maximo"].round(2).tolist())

def rows_disp(df_):
    rows = []
    for _, r in df_.head(20).iterrows():
        teto_f = " <span style='color:#ef4444;font-size:10px'>⚠TETO</span>" if r["acima_teto"] else ""
        rows.append(
            f'<tr><td>{str(r["CARGO"])[:50]}</td>'
            f'<td class="num">{int(r["n"]):,}</td>'
            f'<td class="num">{brl(r["media"])}</td>'
            f'<td class="num green">{brl(r["minimo"])}</td>'
            f'<td class="num red">{brl(r["maximo"])}{teto_f}</td>'
            f'<td class="num bold">{brl(r["amplitude"])}</td>'
            f'<td class="num">{r["cv"]:.0f}%</td></tr>'
        )
    return "\n".join(rows)

# ──────────────────────────────────────────────────────────────────────────
# 4. ANÁLISE 3 — ACÚMULO DE CARGOS (por NOME, com classificação legal)
#
# Framework legal aplicado:
#   Art. 37, XVI, CF/88:
#     Acumulação PERMITIDA:
#       • 2 cargos de professor
#       • 1 cargo de professor + 1 técnico ou científico
#       • 2 cargos/empregos privativos de profissionais de saúde
#       • 1 cargo efetivo + 1 função comissionada (prática administrativa comum)
#     Acumulação PROIBIDA:
#       • Quaisquer outros 3+ cargos/funções remunerados
#   Art. 37, XI, CF/88 (Teto):
#       • Remuneração total não pode exceder o subsídio de Ministro do STF
#   MANDATOS SOCIETÁRIOS (conselhos de estatais):
#       • NÃO são "cargos públicos" — são mandatos de direito privado
#       • Não contam para o limite de 2 cargos
#       • Exemplos: BRB, CAESB, CEB, Metrô-DF, TERRACAP
#   Art. 142, CF/88:
#       • Militares (PMDF/CBMDF) seguem regime próprio
#
#   Classificação desta análise:
#     ILEGAL    → efetivos+comissionados > 2 (sem exceção legal plausível)
#     VERIFICAR → 2 cargos efetivos (pode ser legal: professor, saúde, técnico)
#     TETO      → 1 ou 2 cargos, porém soma ativa > teto constitucional
#     LEGAL     → 1 efetivo + ≤1 comissionado + N conselhos (não exibido)
#
#   Nota: CPF vem pré-mascarado pelo GDF (***XXXXXX**).
#   Agrupamento por NOME. Nomes com ≥5 registros = possível homônimo (⚠).
# ──────────────────────────────────────────────────────────────────────────
print("Verificando acúmulo por NOME (classificação legal refinada)...")

nome_freq    = df["NOME"].value_counts()
nomes_comuns = set(nome_freq[nome_freq >= 5].index)

# Agregação por tipo de vínculo (ativos)
grp_at = (df_at.groupby("NOME")
               .agg(vinculos_at=("CARGO","nunique"), orgaos_at=("ÓRGÃO","nunique"),
                    soma_at=("BRUTO_N","sum"))
               .reset_index())

grp_ef = (df_at[df_at["TIPO_VINC"] == "EFETIVO"]
          .groupby("NOME").agg(n_ef=("CARGO","nunique")).reset_index())

grp_co = (df_at[df_at["TIPO_VINC"] == "COMISSIONADO"]
          .groupby("NOME").agg(n_co=("CARGO","nunique")).reset_index())

grp_cs = (df_at[df_at["TIPO_VINC"] == "CONSELHO"]
          .groupby("NOME").agg(n_cs=("CARGO","nunique")).reset_index())

# Inativos (aposentados, pensionistas…)
df_in = df[~df["IS_ATIVO"]].copy()
grp_in = (df_in.groupby("NOME")
               .agg(vinculos_in=("CARGO","nunique"), soma_in=("BRUTO_N","sum"))
               .reset_index())

# Agrupamento geral
grp_all = (df.groupby("NOME")
             .agg(registros=("BRUTO_N","count"), soma_total=("BRUTO_N","sum"))
             .reset_index())

nome_grp = (grp_all
            .merge(grp_at, on="NOME", how="left")
            .merge(grp_ef, on="NOME", how="left")
            .merge(grp_co, on="NOME", how="left")
            .merge(grp_cs, on="NOME", how="left")
            .merge(grp_in, on="NOME", how="left"))

int_cols = ["vinculos_at","orgaos_at","n_ef","n_co","n_cs","vinculos_in"]
flt_cols = ["soma_at","soma_in"]
nome_grp[int_cols] = nome_grp[int_cols].fillna(0).astype(int)
nome_grp[flt_cols] = nome_grp[flt_cols].fillna(0.0)

def _legal_status(r):
    """
    Classifica a situação legal com base nos vínculos ativos.
    CONSELHO (mandato societário) é excluído do limite de cargos.
    """
    n_ef = r["n_ef"]    # efetivos
    n_co = r["n_co"]    # comissionados
    n_cs = r["n_cs"]    # conselhos (mandatos — não contam)
    total_cargos = n_ef + n_co  # conselhos excluídos

    if total_cargos > 2:
        return "ILEGAL"      # 3+ cargos/funções: proibido Art. 37, XVI
    if n_ef == 2 and n_co == 0:
        return "VERIFICAR"   # 2 efetivos: legal só para prof/prof, prof/téc, saúde/saúde
    if r["soma_at"] > TETO_STF and total_cargos > 1:
        return "TETO"        # acúmulo ultrapassa teto constitucional
    if r["soma_at"] > TETO_STF and total_cargos == 1:
        return "TETO_UNICO"  # 1 cargo mas já acima do teto individualmente
    return "LEGAL"

nome_grp["status"] = nome_grp.apply(_legal_status, axis=1)
nome_grp["possivel_homonimo"] = nome_grp["NOME"].isin(nomes_comuns)

# Apenas casos não-legais para exibição
acumulo = nome_grp[nome_grp["status"] != "LEGAL"].copy()

# Ordenar: não-homônimos ilegais primeiro, depois teto, depois verificar
_priority = {"ILEGAL": 4, "TETO": 3, "VERIFICAR": 2, "TETO_UNICO": 1}
acumulo["_p"] = acumulo["status"].map(_priority).fillna(0)
acumulo["_sort"] = (
    (~acumulo["possivel_homonimo"]).astype(int) * 1_000_000
    + acumulo["_p"] * 100_000
    + (acumulo["soma_at"] / 1e4).clip(0, 99_999)
)
acumulo = acumulo.sort_values("_sort", ascending=False).drop(columns=["_p","_sort"])

n_acumulo      = len(acumulo)
n_ilegais      = int((acumulo["status"] == "ILEGAL").sum())
n_verificar    = int((acumulo["status"] == "VERIFICAR").sum())
n_teto         = int(acumulo["status"].isin({"TETO","TETO_UNICO"}).sum())

print(f"  Acumulação: {n_ilegais} ILEGAIS | {n_verificar} VERIFICAR | {n_teto} TETO")

# Detalhe individual por nome
def detalhe_nome(nome):
    sub = (df[df["NOME"] == nome]
             [["CARGO","ÓRGÃO","BRUTO_N","TIPO_VINC","IS_ATIVO","ACIMA_TETO"]]
             .drop_duplicates(subset=["CARGO","ÓRGÃO","TIPO_VINC"]))
    parts = []
    for _, r in sub.sort_values(["IS_ATIVO","BRUTO_N"], ascending=[False, False]).iterrows():
        tipo  = r["TIPO_VINC"]   # EFETIVO / COMISSIONADO / CONSELHO / INATIVO
        teto_f = " ⚠TETO" if r["ACIMA_TETO"] else ""
        parts.append(
            f"[{tipo}] {str(r['CARGO'])[:28]} @ {str(r['ÓRGÃO'])[:28]} = {brl(r['BRUTO_N'])}{teto_f}"
        )
    return " | ".join(parts)

# Distribuição por tipo de vínculo ativo (para chart)
_tipos_count = df_at["TIPO_VINC"].value_counts()
j_vinc_labels = json.dumps([f"{t}" for t in _tipos_count.index.tolist()])
j_vinc_data   = json.dumps(_tipos_count.tolist())

# Número de cargos efetivos por nome (entre os que têm >1 ativo)
_vd = (acumulo[acumulo["vinculos_at"] > 1]["vinculos_at"]
       .value_counts().sort_index().reset_index())
_vd.columns = ["v","n"]
j_vinc_labels = json.dumps([f"{r} ativo(s)" for r in _vd["v"].tolist()])
j_vinc_data   = json.dumps(_vd["n"].tolist())

# Valores brutos idênticos frequentes (apenas ativos)
vals_dup = (df_at.groupby("BRUTO_N")["NOME"].count().reset_index(name="qtd"))
vals_dup = vals_dup[(vals_dup["BRUTO_N"] > 500) & (vals_dup["qtd"] >= 50)]
vals_dup = vals_dup.sort_values("qtd", ascending=False).head(10)
j_dup_labels = json.dumps([f"R${v:,.0f}".replace(",",".") for v in vals_dup["BRUTO_N"].tolist()])
j_dup_data   = json.dumps(vals_dup["qtd"].tolist())

STATUS_BADGE = {
    "ILEGAL": (
        "background:#7f1d1d;color:#fca5a5",
        "🔴 ILEGAL — >2 cargos/funções"
    ),
    "VERIFICAR": (
        "background:#1e3a5f;color:#93c5fd",
        "🔵 VERIFICAR — 2 efetivos"
    ),
    "TETO": (
        "background:#78350f;color:#fcd34d",
        "🟠 TETO — acúmulo > teto STF"
    ),
    "TETO_UNICO": (
        "background:#78350f;color:#fcd34d",
        "🟠 TETO — cargo único > teto"
    ),
}

def rows_acumulo(df_):
    rows = []
    for _, r in df_.head(35).iterrows():
        st  = r["status"]
        css, label = STATUS_BADGE.get(st, ("background:#334155;color:#94a3b8", st))
        badge = (f"<span style='{css};padding:2px 7px;border-radius:4px;"
                 f"font-size:11px;font-weight:600;white-space:nowrap'>{label}</span>")

        aviso = (" <span style='color:#f59e0b;font-size:11px'>⚠ poss. homônimo</span>"
                 if r["possivel_homonimo"] else "")

        det = detalhe_nome(r["NOME"])

        # Soma ativa principal + soma inativa como sub-info
        soma_html = brl(r["soma_at"])
        if r["vinculos_in"] > 0:
            soma_html += (f"<div style='color:#64748b;font-size:10px;margin-top:2px'>"
                          f"+ {brl(r['soma_in'])} aposen. = {brl(r['soma_total'])}</div>")

        rows.append(
            f'<tr>'
            f'<td style="white-space:nowrap">{badge}</td>'
            f'<td>{r["NOME"]}{aviso}</td>'
            f'<td class="num">{int(r["n_ef"])}</td>'
            f'<td class="num">{int(r["n_co"])}</td>'
            f'<td class="num">{int(r["n_cs"])}</td>'
            f'<td class="num muted">{int(r["vinculos_in"])}</td>'
            f'<td class="num bold red">{soma_html}</td>'
            f'<td class="mono" style="font-size:11px;color:#94a3b8;line-height:1.8">{det}</td>'
            f'</tr>'
        )
    return "\n".join(rows)

# ──────────────────────────────────────────────────────────────────────────
# 5. ANÁLISE 4 — TOP 10 ÓRGÃOS
# ──────────────────────────────────────────────────────────────────────────
print("Top 10 órgãos...")
top10 = (df.groupby("ÓRGÃO")["BRUTO_N"]
           .agg(n="count", total="sum", media="mean", mediana="median", maximo="max")
           .reset_index().sort_values("total", ascending=False).head(10))
top10["pct"] = (top10["total"] / folha_total * 100).round(1)

j_orgao_labels = json.dumps(top10["ÓRGÃO"].str[:45].tolist())
j_orgao_total  = json.dumps(top10["total"].round(2).tolist())
j_orgao_media  = json.dumps(top10["media"].round(2).tolist())

def rows_top10(df_):
    rows = []
    for i, r in enumerate(df_.itertuples(), 1):
        rows.append(
            f'<tr><td class="num muted">#{i}</td>'
            f'<td>{r.ÓRGÃO}</td>'
            f'<td class="num">{int(r.n):,}</td>'
            f'<td class="num bold">{brl(r.total)}</td>'
            f'<td class="num">{brl(r.media)}</td>'
            f'<td class="num">{brl(r.mediana)}</td>'
            f'<td class="num">{brl(r.maximo)}</td>'
            f'<td class="num badge">{r.pct:.1f}%</td></tr>'
        )
    return "\n".join(rows)

# ──────────────────────────────────────────────────────────────────────────
# 6. ANÁLISE 5 — FAIXAS SALARIAIS
# ──────────────────────────────────────────────────────────────────────────
print("Faixas salariais...")
bins   = [0, 3000, 7000, 15000, 30000, float("inf")]
labels = ["Até R$3k","R$3k–R$7k","R$7k–R$15k","R$15k–R$30k","Acima R$30k"]
df["faixa"] = pd.cut(df["BRUTO_N"], bins=bins, labels=labels, right=True)
faixas      = df["faixa"].value_counts().reindex(labels).fillna(0).astype(int)
faixas_pct  = (faixas / total_serv * 100).round(1)
faixas_med  = df.groupby("faixa", observed=True)["BRUTO_N"].mean().reindex(labels).round(2)

j_faixa_labels = json.dumps(labels)
j_faixa_n      = json.dumps(faixas.tolist())
j_faixa_pct    = json.dumps(faixas_pct.tolist())

colors5 = ["#6366f1","#3b82f6","#10b981","#f59e0b","#ef4444"]

def rows_faixas():
    rows = []
    for i, (lab, n, p, m) in enumerate(zip(labels, faixas.tolist(), faixas_pct.tolist(), faixas_med.tolist())):
        bar_w = int(p * 3)
        c = colors5[i]
        rows.append(
            f'<tr>'
            f'<td><span style="color:{c};font-weight:600">{lab}</span></td>'
            f'<td class="num">{n:,}</td>'
            f'<td class="num">{p:.1f}%</td>'
            f'<td class="num muted">{brl(m)}</td>'
            f'<td><div style="background:{c};height:14px;width:{bar_w}px;border-radius:3px"></div></td>'
            f'</tr>'
        )
    return "\n".join(rows)

# ──────────────────────────────────────────────────────────────────────────
# 7. FORMATADORES
# ──────────────────────────────────────────────────────────────────────────
def brl(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",","X").replace(".",",").replace("X",".")
    except Exception:
        return "-"

teto_brl  = brl(TETO_STF)
gerado_em = datetime.now().strftime("%d/%m/%Y às %H:%M")

html_rows_outliers = rows_outliers(outliers)
html_rows_disp     = rows_disp(disp)
html_rows_acumulo  = rows_acumulo(acumulo)
html_rows_top10    = rows_top10(top10)
html_rows_faixas   = rows_faixas()

card_total_serv = f"{total_serv:,}".replace(",",".")
card_folha      = brl(folha_total)
card_media      = brl(media_geral)
card_mediana    = brl(mediana_geral)
card_outliers   = f"{n_outliers:,}".replace(",",".")
card_ilegais    = f"{n_ilegais:,}".replace(",",".")
card_acumulo    = f"{n_acumulo:,}".replace(",",".")
card_orgaos     = str(df["ÓRGÃO"].nunique())
card_cargos     = str(df["CARGO"].nunique())
pct_top5        = f"{top10['total'].head(5).sum()/folha_total*100:.1f}%"

# ──────────────────────────────────────────────────────────────────────────
# 8. CSS / JS
# ──────────────────────────────────────────────────────────────────────────
CSS = """
:root{--navy:#0f172a;--navy2:#1e293b;--navy3:#334155;--blue:#3b82f6;
  --green:#10b981;--red:#ef4444;--orange:#f59e0b;--purple:#8b5cf6;
  --indigo:#6366f1;--text:#e2e8f0;--muted:#94a3b8;--border:#334155;
  --card:#1e293b;--card2:#263348}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--navy);
  color:var(--text);font-size:14px;line-height:1.6}
.header{background:linear-gradient(135deg,#0f172a 0%,#1a2942 50%,#0f2847 100%);
  border-bottom:1px solid var(--border);padding:32px 40px}
.header h1{font-size:26px;font-weight:700;color:#fff;letter-spacing:-.5px}
.header p{color:var(--muted);margin-top:6px;font-size:13px}
.badge-psa{display:inline-block;background:#1d4ed8;color:#93c5fd;font-size:11px;
  font-weight:600;padding:2px 10px;border-radius:99px;letter-spacing:.5px;margin-bottom:10px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:16px;padding:28px 40px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px}
.card .label{font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted)}
.card .value{font-size:22px;font-weight:700;margin-top:4px;color:#fff}
.card .sub{font-size:12px;color:var(--muted);margin-top:2px}
.card.red{border-color:#7f1d1d;background:#1c0a0a}
.card.green{border-color:#064e3b;background:#0a1f18}
.card.blue{border-color:#1e3a5f;background:#0a1626}
.card.orange{border-color:#78350f;background:#1c1005}
.nav{display:flex;gap:8px;padding:0 40px 28px;flex-wrap:wrap}
.nav a{background:var(--card2);border:1px solid var(--border);color:var(--muted);
  padding:6px 16px;border-radius:6px;text-decoration:none;font-size:12px;
  font-weight:500;transition:.2s}
.nav a:hover{background:var(--blue);color:#fff;border-color:var(--blue)}
.section{padding:0 40px 48px}
.section-header{display:flex;align-items:center;gap:12px;margin-bottom:20px;
  padding-bottom:14px;border-bottom:1px solid var(--border)}
.section-header h2{font-size:18px;font-weight:600;color:#fff}
.section-number{width:32px;height:32px;border-radius:8px;display:flex;
  align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0}
.n1{background:#7f1d1d;color:#fca5a5}
.n2{background:#1e3a5f;color:#93c5fd}
.n3{background:#78350f;color:#fcd34d}
.n4{background:#064e3b;color:#6ee7b7}
.n5{background:#3b0764;color:#c4b5fd}
.section-desc{color:var(--muted);font-size:13px;margin-bottom:20px;max-width:900px}
.legal-box{background:#0d1f0d;border:1px solid #166534;border-radius:10px;
  padding:16px 20px;margin-bottom:20px;color:#86efac;font-size:13px;line-height:1.8}
.legal-box strong{color:#4ade80}
.legal-box code{background:#166534;color:#bbf7d0;padding:1px 5px;border-radius:3px;font-size:12px}
.table-wrap{overflow-x:auto;border-radius:10px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{background:var(--navy3)}
thead th{padding:11px 14px;text-align:left;font-size:11px;text-transform:uppercase;
  letter-spacing:.7px;color:var(--muted);white-space:nowrap}
tbody tr{border-top:1px solid var(--border);transition:.15s}
tbody tr:hover{background:var(--card2)}
tbody td{padding:10px 14px;vertical-align:middle}
.num{text-align:right;font-variant-numeric:tabular-nums;font-family:'Courier New',monospace}
.mono{font-family:'Courier New',monospace;font-size:12px;color:var(--muted)}
.muted{color:var(--muted)}
.bold{font-weight:600}
.green{color:var(--green)}
.red{color:var(--red)}
.badge{background:#1e3a5f;color:#93c5fd;padding:2px 8px;border-radius:99px;
  font-weight:600;font-size:12px;text-align:center}
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:28px}
.chart-box{background:var(--card);border:1px solid var(--border);
  border-radius:12px;padding:24px}
.chart-box h3{font-size:13px;font-weight:600;color:var(--muted);
  text-transform:uppercase;letter-spacing:.6px;margin-bottom:16px}
.chart-full{grid-column:1/-1}
.alert{background:#1c0a0a;border:1px solid #7f1d1d;border-radius:10px;
  padding:16px 20px;margin-bottom:20px;color:#fca5a5;font-size:13px}
.alert strong{color:#ef4444}
.warn{background:#1c1005;border:1px solid #78350f;border-radius:10px;
  padding:16px 20px;margin-bottom:20px;color:#fcd34d;font-size:13px}
.info-box{background:#0a1626;border:1px solid #1e3a5f;border-radius:10px;
  padding:16px 20px;margin-bottom:20px;color:#93c5fd;font-size:13px}
.footer{border-top:1px solid var(--border);padding:24px 40px;
  color:var(--muted);font-size:12px;text-align:center}
@media(max-width:900px){
  .header,.cards,.nav,.section{padding-left:16px;padding-right:16px}
  .charts-grid{grid-template-columns:1fr}
}
"""

JS = """
const Cfg = {
  outOrgaoLabels: OUT_ORGAO_LABELS,
  outOrgaoData:   OUT_ORGAO_DATA,
  dispLabels:     DISP_LABELS,
  dispMin:        DISP_MIN,
  dispMedia:      DISP_MEDIA,
  dispMax:        DISP_MAX,
  vincLabels:     VINC_LABELS,
  vincData:       VINC_DATA,
  dupLabels:      DUP_LABELS,
  dupData:        DUP_DATA,
  orgaoLabels:    ORGAO_LABELS,
  orgaoTotal:     ORGAO_TOTAL,
  orgaoMedia:     ORGAO_MEDIA,
  faixaLabels:    FAIXA_LABELS,
  faixaN:         FAIXA_N,
  faixaPct:       FAIXA_PCT
};

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

// Outliers por órgão (ativos)
new Chart(document.getElementById('cOutliers'), {
  type:'bar',
  data:{ labels: Cfg.outOrgaoLabels,
    datasets:[{ label:'Outliers', data: Cfg.outOrgaoData,
      backgroundColor:'rgba(239,68,68,.75)', borderRadius:5 }]},
  options:{ indexAxis:'y', plugins:{legend:{display:false}},
    scales:{ x:{grid:{color:'#1e293b'}}, y:{grid:{color:'#1e293b'},ticks:{font:{size:11}}} }}
});

// Disparidade min/media/max (somente ativos)
new Chart(document.getElementById('cDisp'), {
  type:'bar',
  data:{ labels: Cfg.dispLabels,
    datasets:[
      {label:'Mínimo', data:Cfg.dispMin, backgroundColor:'rgba(16,185,129,.6)', borderRadius:3},
      {label:'Média',  data:Cfg.dispMedia, backgroundColor:'rgba(59,130,246,.8)', borderRadius:3},
      {label:'Máximo', data:Cfg.dispMax, backgroundColor:'rgba(239,68,68,.6)', borderRadius:3}
    ]},
  options:{ indexAxis:'y',
    plugins:{legend:{position:'top'}},
    scales:{
      x:{grid:{color:'#1e293b'},ticks:{callback:v=>'R$'+Number(v).toLocaleString('pt-BR')}},
      y:{grid:{color:'#1e293b'},ticks:{font:{size:11}}}
    }}
});

// Vínculos ativos (distribuição de quantidade)
new Chart(document.getElementById('cVinc'), {
  type:'bar',
  data:{ labels: Cfg.vincLabels,
    datasets:[{label:'Servidores', data:Cfg.vincData,
      backgroundColor:'rgba(245,158,11,.75)', borderRadius:5}]},
  options:{ plugins:{legend:{display:false}},
    scales:{ x:{grid:{color:'#1e293b'}}, y:{grid:{color:'#1e293b'}} }}
});

// Valores idênticos frequentes
new Chart(document.getElementById('cDup'), {
  type:'bar',
  data:{ labels: Cfg.dupLabels,
    datasets:[{label:'Servidores', data:Cfg.dupData,
      backgroundColor:'rgba(139,92,246,.75)', borderRadius:5}]},
  options:{ plugins:{legend:{display:false}},
    scales:{ x:{grid:{color:'#1e293b'},ticks:{font:{size:10}}},
             y:{grid:{color:'#1e293b'}} }}
});

// Top 10 órgãos
new Chart(document.getElementById('cOrgao'), {
  type:'bar',
  data:{ labels: Cfg.orgaoLabels,
    datasets:[
      {label:'Folha Total (R$)', data:Cfg.orgaoTotal,
       backgroundColor:'rgba(59,130,246,.75)', borderRadius:4, yAxisID:'y'},
      {label:'Média (R$)', data:Cfg.orgaoMedia, type:'line', yAxisID:'y2',
       tension:.3, pointRadius:5, borderWidth:2,
       borderColor:'#10b981', backgroundColor:'#10b981', pointBackgroundColor:'#10b981'}
    ]},
  options:{
    plugins:{legend:{position:'top'}},
    scales:{
      x:{grid:{color:'#1e293b'},ticks:{font:{size:11}}},
      y:{grid:{color:'#1e293b'},position:'left',
         ticks:{callback:v=>'R$'+Number(v/1e6).toFixed(0)+'M'}},
      y2:{grid:{display:false},position:'right',
          ticks:{callback:v=>'R$'+Number(v).toLocaleString('pt-BR')}}
    }}
});

// Faixas — bar
new Chart(document.getElementById('cFaixaBar'), {
  type:'bar',
  data:{ labels: Cfg.faixaLabels,
    datasets:[{label:'Servidores', data:Cfg.faixaN,
      backgroundColor:['#6366f1','#3b82f6','#10b981','#f59e0b','#ef4444'],
      borderRadius:6}]},
  options:{ plugins:{legend:{display:false}},
    scales:{ x:{grid:{color:'#1e293b'}},
             y:{grid:{color:'#1e293b'},ticks:{callback:v=>v.toLocaleString('pt-BR')}} }}
});

// Faixas — doughnut
new Chart(document.getElementById('cFaixaDough'), {
  type:'doughnut',
  data:{ labels: Cfg.faixaLabels,
    datasets:[{data:Cfg.faixaPct,
      backgroundColor:['#6366f1','#3b82f6','#10b981','#f59e0b','#ef4444'],
      borderWidth:2, borderColor:'#1e293b'}]},
  options:{ cutout:'60%',
    plugins:{
      legend:{position:'right',labels:{font:{size:12},padding:14}},
      tooltip:{callbacks:{label:ctx=>ctx.label+': '+ctx.parsed.toFixed(1)+'%'}}
    }}
});
"""

JS = (JS
  .replace("OUT_ORGAO_LABELS", j_out_orgao_labels)
  .replace("OUT_ORGAO_DATA",   j_out_orgao_data)
  .replace("DISP_LABELS",      j_disp_labels)
  .replace("DISP_MIN",         j_disp_min)
  .replace("DISP_MEDIA",       j_disp_media)
  .replace("DISP_MAX",         j_disp_max)
  .replace("VINC_LABELS",      j_vinc_labels)
  .replace("VINC_DATA",        j_vinc_data)
  .replace("DUP_LABELS",       j_dup_labels)
  .replace("DUP_DATA",         j_dup_data)
  .replace("ORGAO_LABELS",     j_orgao_labels)
  .replace("ORGAO_TOTAL",      j_orgao_total)
  .replace("ORGAO_MEDIA",      j_orgao_media)
  .replace("FAIXA_LABELS",     j_faixa_labels)
  .replace("FAIXA_N",          j_faixa_n)
  .replace("FAIXA_PCT",        j_faixa_pct)
)

# ──────────────────────────────────────────────────────────────────────────
# 9. HTML FINAL
# ──────────────────────────────────────────────────────────────────────────
html = (
"<!DOCTYPE html>\n"
"<html lang='pt-BR'>\n"
"<head>\n"
"<meta charset='UTF-8'>\n"
"<meta name='viewport' content='width=device-width,initial-scale=1'>\n"
"<title>Auditoria Salarial GDF — Junho/2025</title>\n"
"<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js'></script>\n"
f"<style>{CSS}</style>\n"
"</head>\n<body>\n"

# HEADER
f"<div class='header'>"
f"<div class='badge-psa'>🛡 PSA — PRIVACY SHIELD AGENT</div>"
f"<h1>Auditoria de Remuneração — GDF</h1>"
f"<p>Competência: Junho/2025 &nbsp;·&nbsp; Gerado em {gerado_em} &nbsp;·&nbsp;"
f" Teto constitucional (STF 2025): {teto_brl} &nbsp;·&nbsp;"
f" Dados processados localmente — Protocolo PSA ativo</p>"
f"</div>\n"

# CARDS
f"<div class='cards'>"
f"<div class='card blue'><div class='label'>Total de Servidores</div><div class='value'>{card_total_serv}</div><div class='sub'>Registros na base</div></div>"
f"<div class='card blue'><div class='label'>Folha Total Bruta</div><div class='value'>{card_folha}</div><div class='sub'>Junho/2025</div></div>"
f"<div class='card'><div class='label'>Média Geral Bruta</div><div class='value'>{card_media}</div><div class='sub'>Por servidor</div></div>"
f"<div class='card'><div class='label'>Mediana Geral</div><div class='value'>{card_mediana}</div><div class='sub'>50% ganham menos</div></div>"
f"<div class='card red'><div class='label'>Outliers Salariais</div><div class='value'>{card_outliers}</div><div class='sub'>Ativos acima 2σ no cargo</div></div>"
f"<div class='card red'><div class='label'>ILEGAIS (>2 cargos)</div><div class='value'>{card_ilegais}</div><div class='sub'>Sem exceção legal plausível</div></div>"
f"<div class='card orange'><div class='label'>Casos p/ Verificação</div><div class='value'>{card_acumulo}</div><div class='sub'>ILEGAL · VERIFICAR · TETO</div></div>"
f"<div class='card green'><div class='label'>Órgãos na Base</div><div class='value'>{card_orgaos}</div><div class='sub'>Órgãos distintos</div></div>"
f"</div>\n"

# NAV
"<div class='nav'>"
"<a href='#s1'>🔴 Outliers Salariais</a>"
"<a href='#s2'>📊 Disparidade por Cargo</a>"
"<a href='#s3'>⚠️ Acúmulo / Teto</a>"
"<a href='#s4'>🏛️ Top 10 Órgãos</a>"
"<a href='#s5'>📈 Faixas Salariais</a>"
"</div>\n"

# ── S1 ──────────────────────────────────────────────────────────────────
"<div class='section' id='s1'>"
"<div class='section-header'><div class='section-number n1'>1</div>"
"<h2>Inconsistências Salariais — Outliers por Cargo (Ativos)</h2></div>"
"<p class='section-desc'>Servidores <strong>ativos</strong> com remuneração bruta acima de 2 desvios-padrão (2σ) "
"em relação à média do mesmo cargo. Aposentados excluídos para evitar distorção por pagamentos acumulados "
"(retroativos, 13º, precatórios). Cargos com ≥ 15 servidores ativos. "
"🔴 &gt;4σ &nbsp; 🟠 3–4σ &nbsp; 🟡 2–3σ &nbsp; ⚠TETO = acima do teto constitucional.</p>"
f"<div class='alert'><strong>⚠ {card_outliers} servidores ativos</strong> com remuneração acima de 2σ no cargo. Exibindo os 30 casos com maior afastamento estatístico.</div>"
"<div class='info-box'>ℹ️ CPF pré-mascarado pelo GDF (<code>***XXXXXX**</code>) — todas as análises de identidade agrupam por <strong>NOME</strong>.</div>"
"<div class='charts-grid'>"
"<div class='chart-box chart-full'><h3>Outliers por Órgão (Top 12 — servidores ativos)</h3>"
"<canvas id='cOutliers' height='80'></canvas></div>"
"</div>"
"<div class='table-wrap'><table>"
"<thead><tr><th>Severidade</th><th>Nome</th><th>Cargo</th><th>Órgão</th>"
"<th>Bruto</th><th>Média do Cargo</th><th>Razão</th></tr></thead>"
f"<tbody>{html_rows_outliers}</tbody>"
"</table></div></div>\n"

# ── S2 ──────────────────────────────────────────────────────────────────
"<div class='section' id='s2'>"
"<div class='section-header'><div class='section-number n2'>2</div>"
"<h2>Disparidade Salarial por Cargo — Servidores Ativos</h2></div>"
f"<p class='section-desc'>Amplitude salarial (máximo − mínimo) por cargo, usando apenas servidores ativos. "
f"Aposentados são excluídos: seus pagamentos podem incluir acertos retroativos ou benefícios acumulados "
f"que não refletem o salário mensal corrente. ⚠TETO = máximo supera {teto_brl}. "
f"Apenas cargos com ≥ 20 ativos. CV &gt; 50% indica alta heterogeneidade interna.</p>"
"<div class='charts-grid'>"
"<div class='chart-box chart-full'><h3>Top 15 Cargos — Amplitude Salarial (Ativos: Mín / Média / Máx)</h3>"
"<canvas id='cDisp' height='100'></canvas></div>"
"</div>"
"<div class='table-wrap'><table>"
"<thead><tr><th>Cargo</th><th>Ativos</th><th>Média</th>"
"<th>Mínimo</th><th>Máximo</th><th>Amplitude</th><th>CV%</th></tr></thead>"
f"<tbody>{html_rows_disp}</tbody>"
"</table></div></div>\n"

# ── S3 ──────────────────────────────────────────────────────────────────
"<div class='section' id='s3'>"
"<div class='section-header'><div class='section-number n3'>3</div>"
"<h2>Acúmulo de Cargos e Violações do Teto</h2></div>"

"<div class='legal-box'>"
"<strong>📋 Framework Legal — O que é permitido:</strong><br>"
"<code>LEGAL</code> &nbsp; 1 cargo efetivo + 1 função comissionada + N conselhos de estatais "
"(BRB, CAESB, CEB, Metrô…) &nbsp;→&nbsp; <strong>Situação comum em Brasília</strong>. "
"Conselhos são mandatos societários (direito privado), não cargos públicos — não contam para o limite.<br>"
"<code>LEGAL</code> &nbsp; 2 cargos efetivos se: professor+professor · professor+técnico-científico · "
"profissional de saúde+saúde (Art. 37, XVI, CF/88).<br>"
"<code>VERIFICAR 🔵</code> &nbsp; 2 cargos efetivos sem comissionado — "
"precisa confirmar se enquadrado nas exceções constitucionais.<br>"
"<code>ILEGAL 🔴</code> &nbsp; 3+ cargos/funções simultâneos (efetivos + comissionados) — "
"proibido pela Constituição sem exceção.<br>"
"<code>TETO 🟠</code> &nbsp; Soma dos salários ativos supera o teto constitucional "
f"({teto_brl}) — Art. 37, XI, CF/88.<br>"
"<strong>⚠ Militares</strong> (PMDF/CBMDF) seguem Art. 142, CF/88 e podem ter regras de "
"acumulação distintas. &nbsp;·&nbsp; "
"<strong>⚠ Homônimos</strong>: nomes muito comuns (≥5 registros) podem representar "
"pessoas diferentes — verifique antes de concluir."
"</div>"

f"<div class='alert'>"
f"<strong>🔴 {n_ilegais} nomes com >2 cargos/funções ativos</strong> (ILEGAL — Art. 37, XVI) &nbsp;·&nbsp; "
f"<strong>🔵 {n_verificar} com 2 efetivos</strong> (VERIFICAR — pode ser legal) &nbsp;·&nbsp; "
f"<strong>🟠 {n_teto} com soma ativa acima do teto</strong> ({teto_brl})"
f"</div>"

"<div class='charts-grid'>"
"<div class='chart-box'><h3>Distribuição — Nomes com Múltiplos Vínculos Ativos</h3>"
"<canvas id='cVinc' height='160'></canvas></div>"
"<div class='chart-box'><h3>Valores BRUTO Idênticos Frequentes (Ativos)</h3>"
"<canvas id='cDup' height='160'></canvas></div>"
"</div>"

"<div class='table-wrap'><table>"
"<thead><tr>"
"<th>Status Legal</th>"
"<th>Nome</th>"
"<th title='Cargos efetivos ativos (ATIVO, ATIVO PERMANENTE...)'>Efetivos</th>"
"<th title='Funções comissionadas ativas'>Comiss.</th>"
"<th title='Mandatos em conselhos de estatais — NÃO contam para o limite de cargos'>Conselhos</th>"
"<th title='Aposentadorias / pensões — não contam para o limite'>Aposen.</th>"
"<th>Soma Ativa</th>"
"<th>Detalhe: [Tipo] Cargo @ Órgão = Valor</th>"
"</tr></thead>"
f"<tbody>{html_rows_acumulo}</tbody>"
"</table></div></div>\n"

# ── S4 ──────────────────────────────────────────────────────────────────
"<div class='section' id='s4'>"
"<div class='section-header'><div class='section-number n4'>4</div>"
"<h2>Top 10 Órgãos — Distribuição da Folha</h2></div>"
f"<p class='section-desc'>Top 10 órgãos por folha bruta total (ativos + inativos). Juntos representam {pct_top5} da folha total.</p>"
"<div class='charts-grid'>"
"<div class='chart-box chart-full'><h3>Folha Total e Média por Servidor</h3>"
"<canvas id='cOrgao' height='90'></canvas></div>"
"</div>"
"<div class='table-wrap'><table>"
"<thead><tr><th>#</th><th>Órgão</th><th>Servidores</th><th>Folha Total</th>"
"<th>Média Bruta</th><th>Mediana</th><th>Maior Registro</th><th>% Folha</th></tr></thead>"
f"<tbody>{html_rows_top10}</tbody>"
"</table></div></div>\n"

# ── S5 ──────────────────────────────────────────────────────────────────
"<div class='section' id='s5'>"
"<div class='section-header'><div class='section-number n5'>5</div>"
"<h2>Distribuição por Faixas Salariais</h2></div>"
"<p class='section-desc'>Concentração de servidores por faixa de remuneração bruta mensal (todos os registros).</p>"
"<div class='charts-grid'>"
"<div class='chart-box'><h3>Servidores por Faixa Salarial</h3>"
"<canvas id='cFaixaBar' height='180'></canvas></div>"
"<div class='chart-box'><h3>Proporção por Faixa (%)</h3>"
"<canvas id='cFaixaDough' height='180'></canvas></div>"
"</div>"
"<div class='table-wrap'><table>"
"<thead><tr><th>Faixa</th><th>Servidores</th><th>%</th><th>Média na Faixa</th><th>Proporção</th></tr></thead>"
f"<tbody>{html_rows_faixas}</tbody>"
"</table></div></div>\n"

# FOOTER + JS
f"<div class='footer'>Gerado pelo sistema PSA — Privacy Shield Agent &nbsp;·&nbsp; "
f"Dados processados localmente &nbsp;·&nbsp; {gerado_em} &nbsp;·&nbsp; "
f"Nenhum dado identificável foi transmitido externamente.</div>\n"
f"<script>\n{JS}\n</script>\n"
"</body></html>"
)

OUT_HTML.write_text(html, encoding="utf-8")
print(f"\n✓ Relatório salvo: {OUT_HTML}")
print(f"  Abrir: open '{OUT_HTML}'")
