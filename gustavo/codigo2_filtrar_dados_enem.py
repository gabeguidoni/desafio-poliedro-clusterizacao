import pandas as pd
import numpy as np

# === Caminho do arquivo original ===
caminho_arquivo = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\microdados_enem_2024\DADOS\RESULTADOS_2024.csv"

# === 1. Ler o CSV ===
df = pd.read_csv(caminho_arquivo, sep=';', low_memory=False, encoding='latin1')
print(f"✅ Arquivo carregado: {len(df)} linhas, {len(df.columns)} colunas")

# === 2. Remover colunas desnecessárias ===
colunas_remover = [
    "CO_MUNICIPIO_ESC", "NO_MUNICIPIO_ESC", "CO_UF_ESC", "SG_UF_ESC",
    "TP_LOCALIZACAO_ESC", "CO_MUNICIPIO_PROVA", "NO_MUNICIPIO_PROVA",
    "CO_UF_PROVA", "SG_UF_PROVA", "CO_PROVA_CN", "CO_PROVA_CH",
    "CO_PROVA_LC", "CO_PROVA_MT", "TX_RESPOSTAS_CN", "TX_RESPOSTAS_CH",
    "TX_RESPOSTAS_LC", "TX_RESPOSTAS_MT", "TP_LINGUA", "TX_GABARITO_CN",
    "TX_GABARITO_CH", "TX_GABARITO_LC", "TX_GABARITO_MT", "TP_STATUS_REDACAO",
    "NU_NOTA_COMP1", "NU_NOTA_COMP2", "NU_NOTA_COMP3", "NU_NOTA_COMP4",
    "NU_NOTA_COMP5", "TP_PRESENCA_CN", "TP_PRESENCA_CH", "TP_PRESENCA_LC", "TP_PRESENCA_MT"
]
colunas_existentes = [c for c in colunas_remover if c in df.columns]
df = df.drop(columns=colunas_existentes)
print(f"🧹 {len(colunas_existentes)} colunas desnecessárias removidas")

# === 3. Conversão de tipos ===
colunas_notas = ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]

for col in df.columns:
    if col in colunas_notas:
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')
    else:
        df[col] = pd.to_numeric(df[col], errors='ignore')
        if pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].fillna(0).astype(int)

df = df.replace([np.inf, -np.inf], np.nan)

# === 4. Filtrar linhas válidas ===
df = df.dropna(subset=colunas_notas + ["CO_ESCOLA"])
df["CO_ESCOLA"] = pd.to_numeric(df["CO_ESCOLA"], errors="coerce").fillna(0).astype(int)
df = df[(df["CO_ESCOLA"] != 0) & (df["NU_NOTA_REDACAO"] > 0)]
print(f"✅ Linhas restantes após filtro de notas válidas: {len(df)}")

# === 5. Filtrar apenas escolas privadas/conveniadas ativas ===
if all(col in df.columns for col in ["TP_DEPENDENCIA_ADM_ESC", "TP_SIT_FUNC_ESC"]):
    df = df[
        ((df["TP_DEPENDENCIA_ADM_ESC"] == 2) | (df["TP_DEPENDENCIA_ADM_ESC"] == 4))
        & (df["TP_SIT_FUNC_ESC"] == 1)
    ]
    print(f"🏫 Escolas privadas/conveniadas ativas: {len(df)} registros")
else:
    print("⚠️ Colunas 'TP_DEPENDENCIA_ADM_ESC' e/ou 'TP_SIT_FUNC_ESC' não encontradas no arquivo!")

# === 6. Remover colunas administrativas (mantém NU_ANO e TP_DEPENDENCIA_ADM_ESC) ===
colunas_admin = ["NU_SEQUENCIAL", "TP_SIT_FUNC_ESC"]
df = df.drop(columns=[c for c in colunas_admin if c in df.columns])
print("🧾 Colunas administrativas removidas (NU_ANO e TP_DEPENDENCIA_ADM_ESC mantidos)")

# === 7. Agregar por escola ===
agrupado = (
    df.groupby(["CO_ESCOLA", "NU_ANO", "TP_DEPENDENCIA_ADM_ESC"])
    .agg(
        QT_NOTAS=("CO_ESCOLA", "size"),
        SOMA_NU_NOTA_CN=("NU_NOTA_CN", "sum"),
        SOMA_NU_NOTA_CH=("NU_NOTA_CH", "sum"),
        SOMA_NU_NOTA_LC=("NU_NOTA_LC", "sum"),
        SOMA_NU_NOTA_MT=("NU_NOTA_MT", "sum"),
        SOMA_NU_NOTA_REDACAO=("NU_NOTA_REDACAO", "sum")
    )
    .reset_index()
)

# === 8. Calcular médias individuais (float com duas casas) ===
for col in ["NU_NOTA_CN", "NU_NOTA_CH", "NU_NOTA_LC", "NU_NOTA_MT", "NU_NOTA_REDACAO"]:
    col_soma = f"SOMA_{col}"
    agrupado[f"MEDIA_{col}"] = (agrupado[col_soma] / agrupado["QT_NOTAS"]).round(2)

# === 9. Calcular médias parciais e gerais ===
agrupado["MEDIA_PARCIAL"] = (
    agrupado[["MEDIA_NU_NOTA_CN", "MEDIA_NU_NOTA_CH", "MEDIA_NU_NOTA_LC", "MEDIA_NU_NOTA_MT"]]
    .mean(axis=1)
).round(2)

agrupado["MEDIA_GERAL"] = (
    agrupado[["MEDIA_NU_NOTA_CN", "MEDIA_NU_NOTA_CH", "MEDIA_NU_NOTA_LC", "MEDIA_NU_NOTA_MT", "MEDIA_NU_NOTA_REDACAO"]]
    .mean(axis=1)
).round(2)

# === 10. Converter todas as colunas de nota para float (duas casas decimais) ===
colunas_float = [c for c in agrupado.columns if "SOMA_" in c or "MEDIA_" in c]
agrupado[colunas_float] = agrupado[colunas_float].astype(float).round(2)

# === 11. Salvar arquivo final ===
agrupado.to_csv(
    "01_enem_filtrado.csv",
    sep=';',          # separador de colunas
    decimal=',',      # vírgula decimal compatível com Excel
    index=False,
    encoding='utf-8-sig'
)

print("\n✅ Arquivo salvo como '01_enem_filtrado.csv'")
print(f"📊 Total de escolas agregadas: {len(agrupado)}")
print(agrupado.head(10))