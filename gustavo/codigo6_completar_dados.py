import pandas as pd
import numpy as np

# === Caminho do arquivo ===
arquivo = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\03_dados_filtrados.csv"

# === Ler o arquivo ===
df = pd.read_csv(arquivo, sep=';', low_memory=False)

# === Listas para preenchimento ===
colunas = ["TP_OCUPACAO_GALPAO"]
valores = [0]

# --- Validação ---
if len(colunas) != len(valores):
    raise ValueError("As listas 'colunas' e 'valores' precisam ter o mesmo tamanho!")

# === 1️⃣ Completar valores nulos ===
for coluna, valor in zip(colunas, valores):
    if coluna in df.columns:
        n_antes = df[coluna].isna().sum()
        df[coluna].fillna(valor, inplace=True)
        n_depois = df[coluna].isna().sum()
        print(f"✅ Coluna '{coluna}': {n_antes} valores nulos preenchidos com '{valor}'.")
    else:
        print(f"⚠️ Coluna '{coluna}' não encontrada no arquivo e foi ignorada.")

# === 2️⃣ Condição especial: QT_NOTAS < 10 ===
if "QT_NOTAS" in df.columns:
    condicao = df["QT_NOTAS"] < 10
    colunas_limpar = ["QT_NOTAS", "MEDIA_GERAL", "MEDIA_PARCIAL"]

    for c in colunas_limpar:
        if c in df.columns:
            afetadas = condicao.sum()
            df.loc[condicao, c] = np.nan
            print(f"🧹 Coluna '{c}': {afetadas} linhas com QT_NOTAS < 10 limpas (NaN).")
        else:
            print(f"⚠️ Coluna '{c}' não existe no dataset.")
else:
    print("⚠️ Coluna 'QT_NOTAS' não encontrada — condição especial ignorada.")

# === 3️⃣ Salvar novo arquivo ===
saida = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\04_dados_completos.csv"
df.to_csv(saida, sep=';', index=False)
print(f"\n💾 Arquivo final salvo em: {saida}")
