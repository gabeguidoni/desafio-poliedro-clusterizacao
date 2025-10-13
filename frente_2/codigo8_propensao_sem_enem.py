import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import MiniBatchKMeans  # ⚡ mais rápido

# --- Evita aviso do OpenBLAS ---
os.environ["OPENBLAS_NUM_THREADS"] = "8"

# === 1️⃣ Carregar base ===
arquivo = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\04_dados_completos.csv"
df = pd.read_csv(arquivo, sep=';', low_memory=False)
target = "GUIA"

# === 2️⃣ Filtrar escolas sem notas ===
df_sem_notas = df[df['QT_NOTAS'].isna() | (df['QT_NOTAS'] == 0)].copy()
print(f"🏫 Escolas sem notas do ENEM: {len(df_sem_notas)}")

# === 3️⃣ Colunas de identificação ===
id_cols = [
    "NU_ANO_CENSO", "NO_REGIAO", "SG_UF", "NO_MUNICIPIO",
    "CO_MUNICIPIO", "NO_ENTIDADE", "CO_ENTIDADE",
    "TP_DEPENDENCIA", "CO_CEP", "TP_SITUACAO_FUNCIONAMENTO", "CO_ORGAO_REGIONAL"
]

# === 4️⃣ Colunas irrelevantes (mesmas do modelo anterior) ===
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
    "IN_RESERVA_PCD", "QT_NOTAS", "MEDIA_PARCIAL", "MEDIA_GERAL"
]

# === 5️⃣ Preparar dados ===
df_model = df_sem_notas.drop(columns=cols_ignorar + id_cols, errors='ignore')
num_cols = df_model.select_dtypes(include=['int64', 'float64']).columns.tolist()
df_model = df_model[num_cols].copy()

# Substitui colunas 100% nulas por 0
for c in df_model.columns:
    if df_model[c].isna().all():
        df_model[c] = 0

# === 6️⃣ Imputar e padronizar ===
imputer = SimpleImputer(strategy='mean')
scaler = StandardScaler()
X_scaled = scaler.fit_transform(imputer.fit_transform(df_model))
print(f"✅ Total de colunas usadas no modelo: {X_scaled.shape[1]}")

# === 7️⃣ Rodar MiniBatchKMeans (rápido e estável) ===
print("⚙️  Treinando modelo KMeans (versão rápida)...")
kmeans = MiniBatchKMeans(n_clusters=2, random_state=42, batch_size=2048, n_init=5)
df_sem_notas['cluster'] = kmeans.fit_predict(X_scaled)
print("✅ Clusters gerados com sucesso.")

# === 8️⃣ Identificar cluster aderente ===
cluster_aderente = df_sem_notas[df_sem_notas[target] == 1]['cluster'].mode()[0]
print(f"📍 Cluster dominante das escolas aderentes: {cluster_aderente}")

# === 9️⃣ Calcular propensão ===
centroid = kmeans.cluster_centers_[cluster_aderente]
distancias = np.linalg.norm(X_scaled - centroid, axis=1)
similaridade = 1 - (distancias - distancias.min()) / (distancias.max() - distancias.min())
df_sem_notas['PROPENSAO_%'] = (similaridade * 100).round(2)

# === 🔟 Importância das variáveis ===
centroides = pd.DataFrame(kmeans.cluster_centers_, columns=df_model.columns)
centro_aderente = centroides.loc[cluster_aderente]
media_global = X_scaled.mean(axis=0)
importancias = abs(centro_aderente - media_global)
importancias = pd.Series(importancias, index=df_model.columns).sort_values(ascending=False)

# === 11️⃣ Salvar resultados ===
df_propensao = df_sem_notas.copy()
cols = ['PROPENSAO_%'] + [c for c in df_propensao.columns if c != 'PROPENSAO_%']
df_propensao = df_propensao[cols]

saida_prop = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\06_dados_com_propensao_sem_enem.csv"
saida_pesos = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\06_dados_ponderados_sem_enem.csv"

df_propensao.to_csv(saida_prop, sep=';', index=False)
df_pesos = pd.DataFrame({
    "Variavel": importancias.index,
    "Peso_no_Modelo": importancias.round(3).values
})
df_pesos.to_csv(saida_pesos, sep=';', index=False)

# === 12️⃣ Feedback final ===
print(f"\n💾 Arquivos salvos com sucesso:")
print(f" - {saida_prop}")
print(f" - {saida_pesos}")

print("\n🏫 Top 10 escolas não aderentes com maior propensão:\n")
print(df_propensao[df_propensao['GUIA'] == 0]
      .sort_values(by='PROPENSAO_%', ascending=False)
      .head(10)[['CO_ENTIDADE','NO_ENTIDADE','SG_UF','PROPENSAO_%']])

print("\n📊 Top 10 variáveis com maior peso no cluster aderente:\n")
print(df_pesos.head(10))
