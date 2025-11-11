import pandas as pd

# === Caminho do seu arquivo ===
arquivo = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\04_dados_completos.csv"

# === Ler o arquivo ===
df = pd.read_csv(arquivo, sep=';', low_memory=False)

# === Colunas que você quer deixar de fora da análise ===
cols_ignorar = [
    "IN_VINCULO_SECRETARIA_EDUCACAO","IN_VINCULO_SEGURANCA_PUBLICA","IN_VINCULO_SECRETARIA_SAUDE",
    "IN_VINCULO_OUTRO_ORGAO","IN_PODER_PUBLICO_PARCERIA","TP_PODER_PUBLICO_PARCERIA",
    "IN_FORMA_CONT_TERMO_COLABORA","IN_FORMA_CONT_TERMO_FOMENTO","IN_FORMA_CONT_ACORDO_COOP",
    "IN_FORMA_CONT_PRESTACAO_SERV","IN_FORMA_CONT_COOP_TEC_FIN","IN_FORMA_CONT_CONSORCIO_PUB",
    "IN_FORMA_CONT_MU_TERMO_COLAB","IN_FORMA_CONT_MU_TERMO_FOMENTO","IN_FORMA_CONT_MU_ACORDO_COOP",
    "IN_FORMA_CONT_MU_PREST_SERV","IN_FORMA_CONT_MU_COOP_TEC_FIN","IN_FORMA_CONT_MU_CONSORCIO_PUB",
    "IN_FORMA_CONT_ES_TERMO_COLAB","IN_FORMA_CONT_ES_TERMO_FOMENTO","IN_FORMA_CONT_ES_ACORDO_COOP",
    "IN_FORMA_CONT_ES_PREST_SERV","IN_FORMA_CONT_ES_COOP_TEC_FIN","IN_FORMA_CONT_ES_CONSORCIO_PUB",
    "IN_MANT_ESCOLA_PRIVADA_EMP","IN_MANT_ESCOLA_PRIVADA_ONG","IN_MANT_ESCOLA_PRIVADA_OSCIP",
    "IN_MANT_ESCOLA_PRIV_ONG_OSCIP","IN_MANT_ESCOLA_PRIVADA_SIND","IN_MANT_ESCOLA_PRIVADA_SIST_S",
    "IN_MANT_ESCOLA_PRIVADA_S_FINS","NU_CNPJ_ESCOLA_PRIVADA","NU_CNPJ_MANTENEDORA",
    "TP_REGULAMENTACAO","TP_RESPONSAVEL_REGULAMENTACAO","CO_ESCOLA_SEDE_VINCULADA","CO_IES_OFERTANTE",
    "CO_LINGUA_INDIGENA_3", "CO_LINGUA_INDIGENA_2", "CO_LINGUA_INDIGENA_1", "TP_INDIGENA_LINGUA",
    "IN_RESERVA_PUBLICA", "IN_RESERVA_PPI", "IN_RESERVA_RENDA", "IN_RESERVA_OUTROS", "IN_RESERVA_NENHUMA",
    "IN_RESERVA_PCD"
]

# === Remover da análise ===
df = df.drop(columns=cols_ignorar, errors='ignore')

# === Calcular porcentagem de valores faltantes ===
faltantes = df.isna().mean() * 100

# === Selecionar apenas colunas com algum valor faltante ===
faltantes = faltantes[faltantes > 0].sort_values(ascending=False)

# === Adicionar recomendação de exclusão ===
limite_excluir = 50  # 50% de dados ausentes
relatorio = pd.DataFrame({
    'percentual_faltante': faltantes.round(2),
    'recomendacao': ['Excluir' if v > limite_excluir else 'Manter' for v in faltantes]
})

# === Exibir resumo ===
print(f"Total de colunas analisadas: {len(df.columns)}")
print(f"Colunas com valores faltantes: {len(relatorio)}\n")

print("🧩 Top 20 colunas com mais valores faltantes:\n")
print(relatorio.head(20))

# # === Salvar relatório completo ===
# saida = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\relatorio_faltantes.csv"
# relatorio.to_csv(saida, sep=';', encoding='utf-8', index_label='coluna')
# print(f"\n✅ Relatório completo salvo em: {saida}")
