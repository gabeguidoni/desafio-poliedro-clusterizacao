import pandas as pd

# === Caminhos dos arquivos ===
excel_path = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\Base 2025.xlsx"
csv_path   = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\02_censo_com_enem.csv"

# === 1. Ler arquivos ===
df_excel = pd.read_excel(excel_path)
df_csv = pd.read_csv(csv_path, sep=';', low_memory=False)

# === 2. Colunas de códigos ===
colunas_codigos = ['Código INEP 1', 'Código INEP 2', 'Código INEP 3']

# === 3. Processar colunas individualmente ===
codigos_por_coluna = {}
listas_colunas = []
duplicatas_detalhe = {}

for c in colunas_codigos:
    # Converter para número e limpar
    col = pd.to_numeric(df_excel[c], errors='coerce').dropna().astype(int)
    
    total = len(col)
    unicos = len(col.unique())
    duplicados = total - unicos

    # Guardar duplicatas específicas
    dups = col[col.duplicated(keep=False)].unique().tolist()
    duplicatas_detalhe[c] = dups
    
    codigos_por_coluna[c] = {'total': total, 'unicos': unicos, 'duplicados': duplicados}
    listas_colunas.append(col)

# === 4. Unir todas as colunas para ver duplicatas entre elas ===
todos_codigos = pd.concat(listas_colunas, ignore_index=True)
duplicados_entre_colunas = todos_codigos[todos_codigos.duplicated(keep=False)].unique().tolist()

# === 5. Códigos únicos totais ===
codigos_excel = todos_codigos.unique()

# === 6. Normalizar CSV ===
df_csv['CO_ENTIDADE'] = pd.to_numeric(df_csv['CO_ENTIDADE'], errors='coerce').fillna(0).astype(int)

# === 7. Comparar ===
col_encontrado = df_csv['CO_ENTIDADE'].isin(codigos_excel).astype(int)

# Inserir logo após CO_ENTIDADE
pos = df_csv.columns.get_loc('CO_ENTIDADE') + 1
df_csv.insert(pos, 'GUIA', col_encontrado)

# === 8. Códigos não encontrados ===
codigos_csv = set(df_csv['CO_ENTIDADE'])
nao_encontrados = [c for c in codigos_excel if c not in codigos_csv]

# === 9. Salvar resultado principal ===
df_csv.to_csv(r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\03_dados_filtrados.csv", index=False, sep=';')

# === 10. Prints detalhados ===
print("✅ Processo concluído!\n")

print("📊 Análise das colunas do Excel:")
for coluna, info in codigos_por_coluna.items():
    print(f"   - {coluna}: {info['total']} totais / {info['unicos']} únicos / {info['duplicados']} duplicados")

print(f"\n→ Total de códigos únicos combinados (todas as colunas): {len(codigos_excel)}")
print(f"→ Encontrados no CSV: {col_encontrado.sum()}")
print(f"→ Não encontrados: {len(nao_encontrados)}")

# === 11. Mostrar duplicatas internas ===
print("\n🔁 Duplicatas dentro de cada coluna:")
for coluna, dups in duplicatas_detalhe.items():
    if len(dups) > 0:
        print(f"   - {coluna}: {len(dups)} duplicatas → {dups[:15]}{'...' if len(dups) > 15 else ''}")
    else:
        print(f"   - {coluna}: nenhuma duplicata")

# === 12. Mostrar duplicatas entre colunas ===
if duplicados_entre_colunas:
    print(f"\n⚠️ Códigos que aparecem em mais de uma coluna ({len(duplicados_entre_colunas)} no total):")
    print(duplicados_entre_colunas[:20], "..." if len(duplicados_entre_colunas) > 20 else "")
else:
    print("\n✅ Nenhum código repetido entre colunas diferentes!")

# === 13. Mostrar alguns não encontrados ===
if nao_encontrados:
    print("\n🔎 Alguns códigos não encontrados no CSV:")
    print(nao_encontrados[:20])
else:
    print("\n🎉 Todos os códigos foram encontrados!")
