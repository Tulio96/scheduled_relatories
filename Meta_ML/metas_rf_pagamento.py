import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt

# Carregar os dados
df = pd.read_csv("dados_receita_julho.csv")

# Selecionar as features numéricas e categóricas simples (como CodSuper, CodCobrador)
features_numericas = ['ValCad', 'FaixaAtraso', 'DU']
features_categoricas = ['CodSuper', 'CodCobrador', 'MesPag', 'Segmento']

# Converter categorias para string (para evitar problemas)
for cat_col in features_categoricas:
    df[cat_col] = df[cat_col].astype(str)

# Vamos usar só as features numéricas e codificações simples para categoricas
# Codificar categoricas com label encoding simples (mais rápido que OneHotEncoder)
from sklearn.preprocessing import LabelEncoder
le_super = LabelEncoder()
le_cobrador = LabelEncoder()
le_mes = LabelEncoder()
le_segmento = LabelEncoder()
#le_ano = LabelEncoder()

df['CodSuper_enc'] = le_super.fit_transform(df['CodSuper'])
df['CodCobrador_enc'] = le_cobrador.fit_transform(df['CodCobrador'])
df['MesPag_enc'] = le_mes.fit_transform(df['MesPag'])
df['Segmento_enc'] = le_segmento.fit_transform(df['Segmento'])
#df['AnoPag_enc'] = le_ano.fit_transform(df['AnoPag'])

# Features finais
features = ['ValCad', 'FaixaAtraso', 'DU', 'CodSuper_enc', 'CodCobrador_enc', 'MesPag_enc', 'Segmento_enc']
target = 'ValPago'

# Preencher NAs numéricos com 0
df[features_numericas] = df[features_numericas].fillna(0)
df[target] = df[target].fillna(0)

# Normalizar numéricos
scaler_features = MinMaxScaler()
df[features_numericas] = scaler_features.fit_transform(df[features_numericas])

# Normalizar target
scaler_target = MinMaxScaler()
df[target] = scaler_target.fit_transform(df[[target]])

# Garantir que os campos AnoPag e MesPag sejam inteiros
#df['AnoPag'] = df['AnoPag'].astype(int)
df['MesPag'] = df['MesPag'].astype(int)

#df_treino = df[
    #(df['AnoPag'] < 2025) |
    #((df['AnoPag'] == 2025) & (df['MesPag'] < 6))
#]
df_treino = df[(df['MesPag'] < 7)]
df_maio = df[(df['MesPag'] == 7)]
df_maio = df_maio.drop(columns=['ValPago', 'ValTaxa'])


df_maio.to_csv('dados_maio_pagamento.csv', index=False)

X_train = df_treino[features]
y_train = df_treino[target]
X_maio = df_maio[features]

# Treinar modelo Random Forest
model = RandomForestRegressor(n_estimators=100, max_depth=5,random_state=42)
model.fit(X_train, y_train.values.ravel())

# Prever maio
y_pred_maio = model.predict(X_maio)
y_pred_maio_orig = scaler_target.inverse_transform(y_pred_maio.reshape(-1,1))

df_maio = df_maio.copy()
df_maio['ValReceita_Prevista'] = y_pred_maio_orig

# Agrupar por supervisor somando a previsão
resultado = df_maio.groupby('Responsavel').agg(ValReceita_Prevista=('ValReceita_Prevista', 'sum')).reset_index()

# Adicionar linha total geral
total_geral = pd.DataFrame({
    'Responsavel': ['TOTAL'],
    'ValReceita_Prevista': [resultado['ValReceita_Prevista'].sum()]
})

resultado_final = pd.concat([resultado, total_geral], ignore_index=True)

resultado_final['ValReceita_Prevista'] = resultado_final['ValReceita_Prevista'].round(2)

resultado_final.to_csv('previsao_julho_pagamento.csv', index=False)

print("Arquivo 'previsao_julho_pagamento.csv' salvo com sucesso! 🚀")

# Obter importâncias
importances = model.feature_importances_
feature_names = features

# Ordenar
indices = np.argsort(importances)[::-1]

# Plotar
plt.figure(figsize=(10, 6))
plt.title("Importância das Features - Random Forest")
plt.bar(range(len(importances)), importances[indices], align="center")
plt.xticks(range(len(importances)), [feature_names[i] for i in indices], rotation=45)
plt.ylabel("Importância relativa")
plt.tight_layout()
plt.savefig("importancia_features_rf.png",dpi=300)
