import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.svm import OneClassSVM
from sklearn.model_selection import ParameterGrid


def get_afinidade_df(df_training, use_ml: bool):
    """
    Remove as escolas com ban
    Retorna um df com as colunas CO_ENTIDADE, valor_venda, afinidade, lat, lon
    """
    print("=======> get_afinidade_df()")
    # Remove as escolas banidas
    df_afinidade = df_training[df_training["cliente"] != -1].copy()

    if use_ml:
        df_afinidade["afinidade"] = _ocsvm_prob(df_afinidade)
    else:
        df_afinidade["afinidade"] = 1

    # Mantem apenas as que nao sao clientes
    df_afinidade = df_afinidade[df_afinidade["cliente"] == 0]

    df_afinidade = df_afinidade[
        ["CO_ENTIDADE", "valor_venda", "afinidade", "lat", "lon"]
    ]

    return df_afinidade


def _ocsvm_prob(df, label_col="cliente"):
    """
    Retorna uma lista (len=df) com um score de "quão provável" cada linha é (mais alto = mais parecido
    com os clientes conhecidos, label==1), usando One-Class SVM.

    Entradas mínimas:
      - df: DataFrame
      - label_col: coluna binária (1 = cliente conhecido)
      - pca_var: variância explicada do PCA (use None para desativar PCA)

    Saída:
      - list[float]: scores (decision_function), na mesma ordem do df
    """

    df_pos = df[df[label_col] == 1]

    features = [
        c
        for c in df.select_dtypes(include=[np.number]).columns
        if c not in [label_col, "CO_ENTIDADE", "CO_CEP", "lat", "lon"]
    ]

    X_pos = df_pos[features]
    X_all = df[features]

    steps = [
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("pca", PCA(n_components=0.95)),
    ]

    pre = Pipeline(steps)

    X_pos_proc = pre.fit_transform(X_pos)
    X_all_proc = pre.transform(X_all)

    param_grid = {
        "nu": [0.01, 0.03, 0.05, 0.1],
        "gamma": ["scale", "auto", 0.01, 0.001],
    }

    rng = np.random.default_rng(seed=2025)
    idx = rng.permutation(X_pos_proc.shape[0])
    mid = max(1, X_pos_proc.shape[0] // 2)
    mid = min(mid, X_pos_proc.shape[0] - 1)
    A, B = X_pos_proc[idx[:mid]], X_pos_proc[idx[mid:]]

    # Escolhe parametros que maximizam score medio em positivos "held-out"
    best_score, best_params = -np.inf, None
    for params in ParameterGrid(param_grid):
        oc = OneClassSVM(kernel="rbf", **params)

        oc.fit(A)
        s1 = oc.decision_function(B).mean()

        oc.fit(B)
        s2 = oc.decision_function(A).mean()

        s = max(s1, s2)
        if s > best_score:
            best_score, best_params = s, params

    # Treino final e scores
    oc_final = OneClassSVM(kernel="rbf", **best_params)
    oc_final.fit(X_pos_proc)
    scores = oc_final.decision_function(X_all_proc)

    # normalização para [0, 1]
    s_min = scores.min()
    s_max = scores.max()

    if s_max == s_min:
        probs = np.zeros_like(scores)
    else:
        probs = (scores - s_min) / (s_max - s_min)

    return probs
