import pandas as pd

# === Caminho do arquivo ===
arquivo = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\microdados_censo_escolar_2024\dados\microdados_ed_basica_2024.csv"

print("🔹 Carregando arquivo...")
df = pd.read_csv(arquivo, sep=';', low_memory=False, encoding='latin-1')

# === Colunas a remover ===
colunas_excluir = [
    "CO_REGIAO", "NO_UF", "CO_UF",
    "NO_REGIAO_GEOG_INTERM", "CO_REGIAO_GEOG_INTERM",
    "NO_REGIAO_GEOG_IMED", "CO_REGIAO_GEOG_IMED",
    "NO_MESORREGIAO", "CO_MESORREGIAO",
    "NO_MICRORREGIAO", "CO_MICRORREGIAO",
    "NO_DISTRITO", "CO_DISTRITO",
    "DS_ENDERECO", "NU_ENDERECO", "DS_COMPLEMENTO",
    "NO_BAIRRO", "NU_DDD", "NU_TELEFONE", "DT_ANO_LETIVO_INICIO",
    "DT_ANO_LETIVO_TERMINO"
]

# Remove apenas as colunas que existirem
df = df.drop(columns=[c for c in colunas_excluir if c in df.columns])

# === Filtragem ===
print("🔹 Filtrando escolas com TP_SITUACAO_FUNCIONAMENTO = 1...")
df = df[df["TP_SITUACAO_FUNCIONAMENTO"] == 1]

# Filtro 1: escolas privadas (TP_DEPENDENCIA = 4)
filtro_geral = df["TP_DEPENDENCIA"] == 4

# Filtro 2: escolas militares (TP_DEPENDENCIA = 2 e nome contém 'MILITAR')
filtro_militar = (df["TP_DEPENDENCIA"] == 2) & (df["NO_ENTIDADE"].str.contains("MILITAR", case=False, na=False))

# Combina os dois filtros
df_filtrado = df[filtro_geral | filtro_militar]

# === Resultado final ===
print(f"✅ Total de escolas filtradas: {len(df_filtrado):,}")

# === Salvar resultado ===
saida = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\01_censo_filtrado.csv"
df_filtrado.to_csv(saida, index=False, sep=';', encoding='utf-8-sig')
print(f"💾 Arquivo salvo em:\n{saida}")
