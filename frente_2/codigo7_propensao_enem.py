import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# === 1️⃣ Carregar base ===
arquivo = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\04_dados_completos.csv"
df = pd.read_csv(arquivo, sep=';', low_memory=False)
target = "GUIA"

# === 2️⃣ Filtrar apenas escolas com notas do ENEM ===
df_com_notas = df[df['QT_NOTAS'].notna() & (df['QT_NOTAS'] > 0)].copy()
print(f"🎓 Escolas com notas do ENEM: {len(df_com_notas)}")

# === 3️⃣ Corrigir vírgulas decimais e converter para float ===
for c in ['MEDIA_PARCIAL', 'MEDIA_GERAL']:
    if c in df_com_notas.columns:
        df_com_notas[c] = (
            df_com_notas[c]
            .astype(str)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        df_com_notas[c] = pd.to_numeric(df_com_notas[c], errors='coerce')

# === 4️⃣ Colunas de identificação ===
id_cols = [
    "NU_ANO_CENSO", "NO_REGIAO", "SG_UF", "NO_MUNICIPIO",
    "CO_MUNICIPIO", "NO_ENTIDADE", "CO_ENTIDADE",
    "TP_DEPENDENCIA", "CO_CEP", "TP_SITUACAO_FUNCIONAMENTO", "CO_ORGAO_REGIONAL"
]

# === 5️⃣ Colunas irrelevantes ===
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

# === 6️⃣ Preparar dados numéricos ===
df_model = df_com_notas.drop(columns=cols_ignorar + id_cols, errors='ignore')
num_cols = df_model.select_dtypes(include=['int64', 'float64']).columns.tolist()

# Garante presença das colunas mais importantes
for c in ["QT_NOTAS", "MEDIA_PARCIAL", "MEDIA_GERAL"]:
    if c not in num_cols and c in df_com_notas.columns:
        num_cols.append(c)

df_model = df_model[num_cols].copy()

# Preenche colunas totalmente vazias com 0 (só pra manter estrutura)
for c in df_model.columns:
    if df_model[c].isna().all():
        df_model[c] = 0

# === 7️⃣ Imputar e padronizar ===
imputer = SimpleImputer(strategy='mean')
scaler = StandardScaler()
X_imputed = imputer.fit_transform(df_model)
X_scaled = scaler.fit_transform(X_imputed)
print(f"✅ Total de colunas usadas no modelo: {X_scaled.shape[1]}")

# === 8️⃣ Determinar número ótimo de clusters (Silhouette) ===
range_n = range(2, 8)
scores = []
for k in range_n:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    scores.append(silhouette_score(X_scaled, km.labels_))
best_k = range_n[np.argmax(scores)]
print(f"🔹 Melhor número de clusters pelo Silhouette: {best_k}")

# === 9️⃣ Rodar KMeans final ===
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=20)
df_com_notas['cluster'] = kmeans.fit_predict(X_scaled)

# === 🔟 Identificar cluster aderente ===
cluster_aderente = df_com_notas[df_com_notas[target] == 1]['cluster'].mode()[0]
print(f"📍 Cluster dominante das escolas aderentes: {cluster_aderente}")

# === 11️⃣ Calcular propensão ===
centroid = kmeans.cluster_centers_[cluster_aderente]
distancias = np.linalg.norm(X_scaled - centroid, axis=1)
similaridade = 1 - (distancias - distancias.min()) / (distancias.max() - distancias.min())
df_com_notas['PROPENSAO_%'] = (similaridade * 100).round(2)

# === 12️⃣ Calcular importância das variáveis ===
centroides = pd.DataFrame(kmeans.cluster_centers_, columns=df_model.columns)
centro_aderente = centroides.loc[cluster_aderente]
media_global = X_scaled.mean(axis=0)
importancias = abs(centro_aderente - media_global)
importancias = pd.Series(importancias, index=df_model.columns).sort_values(ascending=False)

# === 13️⃣ Gerar saída 1: dados com propensão ===
df_propensao = df_com_notas.copy()
cols = ['PROPENSAO_%'] + [c for c in df_propensao.columns if c != 'PROPENSAO_%']
df_propensao = df_propensao[cols]
saida_propensao = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\05_dados_com_propensao.csv"
df_propensao.to_csv(saida_propensao, sep=';', index=False)

# === 14️⃣ Gerar saída 2: pesos ===
df_pesos = pd.DataFrame({
    "Variavel": importancias.index,
    "Peso_no_Modelo": importancias.round(3).values
})
saida_pesos = r"C:\Users\zzind\OneDrive\Documents\Gustavo\RPVMM\05_dados_ponderados.csv"
df_pesos.to_csv(saida_pesos, sep=';', index=False)

# === 15️⃣ Feedback final ===
print(f"\n💾 Arquivos salvos com sucesso:")
print(f" - {saida_propensao}")
print(f" - {saida_pesos}")

print("\n🏫 Top 10 escolas não aderentes com maior propensão:\n")
print(df_propensao[df_propensao['GUIA'] == 0]
      .sort_values(by='PROPENSAO_%', ascending=False)
      .head(10)[['CO_ENTIDADE','NO_ENTIDADE','SG_UF','PROPENSAO_%']])

print("\n📊 Top 10 variáveis com maior peso no cluster aderente:\n")
print(df_pesos.head(10))
