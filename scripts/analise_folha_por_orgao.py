"""
PSA - Análise gerada pelo CFO
Solicitação: Distribuição salarial por órgão — Top 5 por folha de pagamento
Execução: local com dados reais em data/real/
Resultados: data/results/
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "real" / "remuneracao202506.csv"
OUT_DIR = BASE_DIR / "results"
OUT_DIR.mkdir(exist_ok=True)

# --- Leitura dos dados reais ---
df = pd.read_csv(DATA_PATH, dtype=str, encoding="latin-1", sep=";")

def parse_br(col):
    """Converte formato brasileiro (1.234,56) para float."""
    return (
        col.str.strip()
           .str.replace(r"\.", "", regex=True)
           .str.replace(",", ".", regex=False)
           .replace("", "0")
           .fillna("0")
           .astype(float)
    )

df["BRUTO_NUM"]  = parse_br(df["BRUTO"])
df["BASICA_NUM"] = parse_br(df["REMUNERAÇÃO BÁSICA"])

# --- Análise por órgão ---
orgao = (
    df.groupby("ÓRGÃO")
    .agg(
        total_servidores=("BRUTO_NUM", "count"),
        folha_total=("BRUTO_NUM", "sum"),
        media_bruto=("BRUTO_NUM", "mean"),
        media_basica=("BASICA_NUM", "mean"),
        mediana_bruto=("BRUTO_NUM", "median"),
        maior_salario=("BRUTO_NUM", "max"),
        menor_salario=("BRUTO_NUM", "min"),
    )
    .reset_index()
    .sort_values("folha_total", ascending=False)
)

top5 = orgao.head(5).copy()

# --- Exibição ---
print("\n" + "=" * 80)
print("ANÁLISE DE FOLHA DE PAGAMENTO — JUNHO/2025")
print("Fonte: remuneracao202506.csv | Competência: Junho 2025")
print(f"Total de servidores na base: {len(df):,}".replace(",", "."))
print(f"Folha total (todos os órgãos): R$ {df['BRUTO_NUM'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
print("=" * 80)

print("\n📊 TOP 5 ÓRGÃOS — MAIOR FOLHA DE PAGAMENTO\n")
for rank, row in enumerate(top5.itertuples(), 1):
    print(f"{'─' * 78}")
    print(f"#{rank}  {row.ÓRGÃO}")
    print(f"    Servidores     : {int(row.total_servidores):>8,}".replace(",", "."))
    print(f"    Folha total    : R$ {row.folha_total:>14,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"    Média bruta    : R$ {row.media_bruto:>10,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"    Média básica   : R$ {row.media_basica:>10,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"    Mediana bruta  : R$ {row.mediana_bruto:>10,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    print(f"    Maior salário  : R$ {row.maior_salario:>10,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

print(f"{'─' * 78}")

# --- Participação percentual na folha total ---
folha_total_geral = df["BRUTO_NUM"].sum()
print("\n📈 PARTICIPAÇÃO NA FOLHA TOTAL\n")
for rank, row in enumerate(top5.itertuples(), 1):
    pct = row.folha_total / folha_total_geral * 100
    bar = "█" * int(pct / 2)
    print(f"  #{rank} {bar:<25} {pct:5.1f}%  {row.ÓRGÃO[:55]}")

pct_top5 = top5["folha_total"].sum() / folha_total_geral * 100
print(f"\n  Top 5 representam {pct_top5:.1f}% da folha total.")

# --- Salvar Excel com ranking completo ---
out_path = OUT_DIR / "folha_por_orgao_202506.xlsx"
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    # Aba 1: Top 5
    top5_fmt = top5.copy()
    for col in ["folha_total","media_bruto","media_basica","mediana_bruto","maior_salario","menor_salario"]:
        top5_fmt[col] = top5_fmt[col].map(lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X","."))
    top5_fmt.to_excel(writer, sheet_name="Top5_Orgaos", index=False)

    # Aba 2: Ranking completo
    orgao_fmt = orgao.copy()
    for col in ["folha_total","media_bruto","media_basica","mediana_bruto","maior_salario","menor_salario"]:
        orgao_fmt[col] = orgao_fmt[col].map(lambda x: f"R$ {x:,.2f}".replace(",","X").replace(".",",").replace("X","."))
    orgao_fmt.to_excel(writer, sheet_name="Ranking_Completo", index=False)

    # Aba 3: Distribuição por faixa salarial (top 5)
    faixas = pd.cut(
        df[df["ÓRGÃO"].isin(top5["ÓRGÃO"])]["BRUTO_NUM"],
        bins=[0, 3000, 6000, 10000, 15000, 20000, float("inf")],
        labels=["Até 3k", "3k–6k", "6k–10k", "10k–15k", "15k–20k", "Acima 20k"]
    ).value_counts().sort_index().reset_index()
    faixas.columns = ["Faixa", "Quantidade"]
    faixas.to_excel(writer, sheet_name="Distribuicao_Faixas", index=False)

print(f"\n✓ Relatório Excel salvo: {out_path}\n")
