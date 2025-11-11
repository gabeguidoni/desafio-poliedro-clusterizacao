import pandas as pd

# === Caminhos dos arquivos ===
microdados_path = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\01_censo_filtrado.csv"
enem_path = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\01_enem_filtrado.csv"
saida_path = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\02_censo_com_enem.csv"

# === 1. Carregar os arquivos ===
df_micro = pd.read_csv(microdados_path, sep=';', low_memory=False)
df_enem = pd.read_csv(enem_path, sep=';', low_memory=False)

# === 2. Selecionar colunas relevantes do ENEM ===
colunas_enem = ['CO_ESCOLA', 'QT_NOTAS', 'MEDIA_PARCIAL', 'MEDIA_GERAL']
df_enem = df_enem[colunas_enem]

# === 3. Fazer o merge (junção) ===
df_resultado = pd.merge(
    df_micro,
    df_enem,
    how='left',  # mantém todas as escolas do microdados, mesmo se não tiver ENEM
    left_on='CO_ENTIDADE',
    right_on='CO_ESCOLA'
)

# === 4. Remover a coluna CO_ESCOLA (já não é mais necessária) ===
df_resultado = df_resultado.drop(columns=['CO_ESCOLA'])

# === 5. Reordenar as colunas: colocar QT_NOTAS, MEDIA_PARCIAL e MEDIA_GERAL logo após CO_ENTIDADE ===
colunas = list(df_resultado.columns)
idx = colunas.index('CO_ENTIDADE')
novas_colunas = colunas[:idx+1] + ['QT_NOTAS', 'MEDIA_PARCIAL', 'MEDIA_GERAL'] + [c for c in colunas[idx+1:] if c not in ['QT_NOTAS', 'MEDIA_PARCIAL', 'MEDIA_GERAL']]
df_resultado = df_resultado[novas_colunas]

# === 6. Salvar o resultado final ===
df_resultado.to_csv(saida_path, sep=';', index=False)

print(f"✅ Arquivo salvo com sucesso em: {saida_path}")
