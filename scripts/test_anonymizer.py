"""
PSA - Privacy Shield Agent
Script: test_anonymizer.py

Teste de ponta a ponta do fluxo de anonimização:
  1. Gera planilha fake com 50 clientes em data/real/teste_clientes.xlsx
  2. Roda o anonymizer.py na planilha gerada
  3. Valida o resultado: estrutura, ausência de dados reais, mapa de correspondência

Uso:
  python3 scripts/test_anonymizer.py
"""

import sys
import json
import re
from pathlib import Path

import pandas as pd
from faker import Faker

# Adiciona o diretório raiz ao path para importar o anonymizer
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from anonymizer import anonymize_spreadsheet

fake = Faker("pt_BR")
Faker.seed(0)

REAL_DIR = BASE_DIR / "data" / "real"
REAL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers para geração de CPF e CNPJ válidos
# ---------------------------------------------------------------------------

def gerar_cpf() -> str:
    digits = [fake.random_int(0, 9) for _ in range(9)]
    for _ in range(2):
        s = sum((len(digits) + 1 - i) * v for i, v in enumerate(digits))
        d = (s * 10 % 11) % 10
        digits.append(d)
    return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*digits)


# ---------------------------------------------------------------------------
# Geração da planilha de teste
# ---------------------------------------------------------------------------

def gerar_planilha_clientes(n: int = 50) -> Path:
    print(f"\n[1/3] Gerando planilha com {n} clientes fictícios...")

    registros = []
    for _ in range(n):
        primeiro = fake.first_name()
        ultimo = fake.last_name()
        nome = f"{primeiro} {ultimo}"
        email = f"{primeiro.lower()}.{ultimo.lower()}@{fake.free_email_domain()}"

        registros.append({
            "nome":        nome,
            "cpf":         gerar_cpf(),
            "email":       email,
            "telefone":    fake.phone_number(),
            "salario":     round(fake.random.uniform(1500, 25000), 2),
            "endereco":    fake.street_address(),
            "bairro":      fake.bairro(),
            "cidade":      fake.city(),
            "estado":      fake.estado_sigla(),
            "cep":         fake.postcode(),
            "data_nasc":   str(fake.date_of_birth(minimum_age=18, maximum_age=65)),
            "cargo":       fake.job(),
            "departamento":fake.random_element(["RH", "TI", "Financeiro", "Comercial", "Operações"]),
            "ativo":       fake.random_element(["Sim", "Não"]),
        })

    df = pd.DataFrame(registros)
    output_path = REAL_DIR / "teste_clientes.xlsx"
    df.to_excel(output_path, index=False)

    print(f"   Planilha salva em: {output_path}")
    print(f"   {len(df)} linhas, {len(df.columns)} colunas: {list(df.columns)}")
    return output_path


# ---------------------------------------------------------------------------
# Execução da anonimização
# ---------------------------------------------------------------------------

def rodar_anonimizacao(input_path: Path) -> tuple[Path, Path]:
    print("\n[2/3] Executando anonimização via PSA Guardião...")
    anon_path, map_path = anonymize_spreadsheet(input_path, sample_size=100)
    print(f"   Arquivo anonimizado: {anon_path}")
    print(f"   Mapa gerado:         {map_path}")
    return anon_path, map_path


# ---------------------------------------------------------------------------
# Validação do resultado
# ---------------------------------------------------------------------------

def validar_resultado(
    original_path: Path,
    anon_path: Path,
    map_path: Path,
) -> bool:
    print("\n[3/3] Validando resultado...")

    erros = []
    avisos = []

    # --- Carregar arquivos ---
    df_orig = pd.read_excel(original_path, dtype=str)
    df_anon = pd.read_excel(anon_path, dtype=str)

    with open(map_path, encoding="utf-8") as f:
        mapa = json.load(f)

    # --- 1. Verificar colunas renomeadas ---
    colunas_anon = set(df_anon.columns)
    colunas_esperadas = {code for code in mapa["colunas"].keys()}
    if not colunas_esperadas.issubset(colunas_anon):
        faltando = colunas_esperadas - colunas_anon
        erros.append(f"Colunas esperadas ausentes no arquivo anonimizado: {faltando}")
    else:
        print("   ✓ Colunas renomeadas corretamente para códigos genéricos")

    # --- 2. Nenhuma coluna original deve aparecer no arquivo anonimizado ---
    colunas_originais = set(df_orig.columns)
    colunas_expostas = colunas_originais & colunas_anon
    if colunas_expostas:
        erros.append(f"Colunas originais ainda presentes no arquivo anonimizado: {colunas_expostas}")
    else:
        print("   ✓ Nenhuma coluna com nome original exposta")

    # --- 3. Verificar que dados sensíveis foram substituídos ---
    colunas_sensiveis = [
        (info["nome_original"], col_code)
        for col_code, info in mapa["colunas"].items()
        if info["anonimizada"]
    ]

    vazamentos = []
    for nome_orig, col_code in colunas_sensiveis:
        if nome_orig not in df_orig.columns or col_code not in df_anon.columns:
            continue
        orig_vals = set(df_orig[nome_orig].dropna().astype(str))
        anon_vals = set(df_anon[col_code].dropna().astype(str))
        # Encontrar valores que vazaram (ignora strings muito curtas que podem coincidir)
        overlap = {v for v in (orig_vals & anon_vals) if len(v) > 4}
        if overlap:
            vazamentos.append((nome_orig, col_code, list(overlap)[:2]))

    if vazamentos:
        for nome_orig, col_code, exemplos in vazamentos:
            avisos.append(f"Possível vazamento em '{nome_orig}' ({col_code}): {exemplos}")
    else:
        print("   ✓ Nenhum valor original encontrado nas colunas sensíveis anonimizadas")

    # --- 4. Verificar padrões de CPF reais ---
    cpf_pattern = re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}")
    orig_cpfs = set()
    if "cpf" in df_orig.columns:
        for v in df_orig["cpf"].dropna():
            m = cpf_pattern.findall(str(v))
            orig_cpfs.update(m)

    cpf_col = next(
        (code for code, info in mapa["colunas"].items() if info["nome_original"] == "cpf"),
        None
    )
    if cpf_col and orig_cpfs:
        anon_text = df_anon[cpf_col].astype(str).str.cat(sep=" ")
        cpfs_expostos = [cpf for cpf in orig_cpfs if cpf in anon_text]
        if cpfs_expostos:
            erros.append(f"CPFs reais encontrados no arquivo anonimizado: {cpfs_expostos[:2]}")
        else:
            print("   ✓ Nenhum CPF real detectado no arquivo anonimizado")

    # --- 5. Verificar emails reais ---
    email_pattern = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    orig_emails = set()
    if "email" in df_orig.columns:
        for v in df_orig["email"].dropna():
            m = email_pattern.findall(str(v))
            orig_emails.update(m)

    email_col = next(
        (code for code, info in mapa["colunas"].items() if info["nome_original"] == "email"),
        None
    )
    if email_col and orig_emails:
        anon_text = df_anon[email_col].astype(str).str.cat(sep=" ")
        emails_expostos = [e for e in orig_emails if e in anon_text]
        if emails_expostos:
            erros.append(f"Emails reais encontrados no arquivo anonimizado: {emails_expostos[:2]}")
        else:
            print("   ✓ Nenhum email real detectado no arquivo anonimizado")

    # --- 6. Verificar mapa de correspondência ---
    campos_obrigatorios = ["timestamp", "arquivo_original", "arquivo_anonimizado", "colunas"]
    faltando_mapa = [c for c in campos_obrigatorios if c not in mapa]
    if faltando_mapa:
        erros.append(f"Mapa de correspondência incompleto. Faltando: {faltando_mapa}")
    else:
        print("   ✓ Mapa de correspondência completo e válido")

    # --- 7. Verificar contagem de linhas ---
    linhas_orig = mapa["total_linhas_original"]
    linhas_anon = mapa["total_linhas_amostra"]
    print(f"   ✓ Linhas originais: {linhas_orig} → Amostra anonimizada: {linhas_anon}")

    # --- Resultado final ---
    print("\n" + "=" * 60)
    if erros:
        print("RESULTADO: FALHOU")
        print(f"  {len(erros)} erro(s) encontrado(s):")
        for e in erros:
            print(f"  ✗ {e}")
    else:
        print("RESULTADO: PASSOU")

    if avisos:
        print(f"\n  {len(avisos)} aviso(s):")
        for a in avisos:
            print(f"  ⚠ {a}")

    print("=" * 60)

    # --- Exibir amostra do arquivo anonimizado ---
    print("\nAmostra do arquivo anonimizado (5 primeiras linhas):")
    print(df_anon.head().to_string())

    print("\nMapa de colunas:")
    for code, info in mapa["colunas"].items():
        status = "anonimizada" if info["anonimizada"] else "mantida"
        print(f"  {code:8} ← {info['nome_original']:20} ({info.get('tipo_sensivel') or 'não-sensível'}, {status})")

    return len(erros) == 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("PSA — TESTE DE ANONIMIZAÇÃO DE PLANILHA")
    print("=" * 60)

    try:
        # 1. Gerar planilha fake
        original_path = gerar_planilha_clientes(n=50)

        # 2. Anonimizar
        anon_path, map_path = rodar_anonimizacao(original_path)

        # 3. Validar
        sucesso = validar_resultado(original_path, anon_path, map_path)

        sys.exit(0 if sucesso else 1)

    except Exception as e:
        print(f"\n[ERRO] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
