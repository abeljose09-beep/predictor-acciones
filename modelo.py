import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import json, sys

# ── Acción a analizar (se puede cambiar desde la interfaz) ─────────────────
ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

# ── Descargar datos ────────────────────────────────────────────────────────
df = yf.download(ticker, start="2015-01-01", end="2024-12-31", auto_adjust=True)
df.columns = df.columns.get_level_values(0)
df.dropna(inplace=True)
df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
for col in df.columns:
    df[col] = df[col].astype(float)

# ── Indicadores ───────────────────────────────────────────────────────────
df['SMA_20'] = df['Close'].rolling(20).mean()
df['SMA_50'] = df['Close'].rolling(50).mean()
df['SMA_ratio'] = df['SMA_20'] / df['SMA_50']
delta = df['Close'].diff()
gain = delta.where(delta > 0, 0).rolling(14).mean()
loss = -delta.where(delta < 0, 0).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss))
ema12 = df['Close'].ewm(span=12).mean()
ema26 = df['Close'].ewm(span=26).mean()
df['MACD'] = ema12 - ema26
df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
df['MACD_diff'] = df['MACD'] - df['MACD_signal']
df['Return_1d'] = df['Close'].pct_change()
df['Return_5d'] = df['Close'].pct_change(5)
df['Return_10d'] = df['Close'].pct_change(10)
df['Volatility'] = df['Return_1d'].rolling(10).std()
df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
df.dropna(inplace=True)

features = ['Open','High','Low','Close','Volume','SMA_20','SMA_50',
            'SMA_ratio','RSI','MACD','MACD_signal','MACD_diff',
            'Return_1d','Return_5d','Return_10d','Volatility']

X = df[features]
y = df['Target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

modelo = RandomForestClassifier(n_estimators=500, max_depth=6,
                                 min_samples_leaf=20, class_weight='balanced', random_state=42)
modelo.fit(X_train, y_train)

# ── Simulación ────────────────────────────────────────────────────────────
umbral = 0.65
probabilidades = modelo.predict_proba(X_test)
capital = 10000.0
capital_bh = 10000.0
historial = []
precio_inicio = df.loc[X_test.index[0], 'Close']

for i, (fecha, prob) in enumerate(zip(X_test.index, probabilidades)):
    precio_hoy = df.loc[fecha, 'Close']
    loc = df.index.get_loc(fecha)
    if loc + 1 >= len(df):
        continue
    precio_manana = df['Close'].iloc[loc + 1]
    retorno = float((precio_manana - precio_hoy) / precio_hoy)

    if prob[1] >= umbral:
        señal = 'COMPRAR'
        capital *= (1 + retorno)
    elif prob[0] >= umbral:
        señal = 'VENDER'
        capital *= (1 - retorno * 0.5)
    else:
        señal = 'ESPERAR'

    historial.append({
        'fecha': str(fecha.date()),
        'precio': round(float(precio_hoy), 2),
        'señal': señal,
        'prob_sube': round(float(prob[1]), 3),
        'prob_baja': round(float(prob[0]), 3),
        'capital': round(capital, 2)
    })

capital_bh = 10000 * (float(df['Close'].iloc[-1]) / float(precio_inicio))

# ── Predicción mañana ─────────────────────────────────────────────────────
df_rec = yf.download(ticker, period="3mo", auto_adjust=True)
df_rec.columns = df_rec.columns.get_level_values(0)
for col in df_rec.columns:
    df_rec[col] = df_rec[col].astype(float)
df_rec['SMA_20'] = df_rec['Close'].rolling(20).mean()
df_rec['SMA_50'] = df_rec['Close'].rolling(50).mean()
df_rec['SMA_ratio'] = df_rec['SMA_20'] / df_rec['SMA_50']
d2 = df_rec['Close'].diff()
g2 = d2.where(d2 > 0, 0).rolling(14).mean()
l2 = -d2.where(d2 < 0, 0).rolling(14).mean()
df_rec['RSI'] = 100 - (100 / (1 + g2 / l2))
e12 = df_rec['Close'].ewm(span=12).mean()
e26 = df_rec['Close'].ewm(span=26).mean()
df_rec['MACD'] = e12 - e26
df_rec['MACD_signal'] = df_rec['MACD'].ewm(span=9).mean()
df_rec['MACD_diff'] = df_rec['MACD'] - df_rec['MACD_signal']
df_rec['Return_1d'] = df_rec['Close'].pct_change()
df_rec['Return_5d'] = df_rec['Close'].pct_change(5)
df_rec['Return_10d'] = df_rec['Close'].pct_change(10)
df_rec['Volatility'] = df_rec['Return_1d'].rolling(10).std()
df_rec.dropna(inplace=True)

prob_hoy = modelo.predict_proba(df_rec[features].iloc[-1:])[0]
precio_actual = float(df_rec['Close'].iloc[-1])

if prob_hoy[1] >= umbral:
    señal_hoy = 'COMPRAR'
elif prob_hoy[0] >= umbral:
    señal_hoy = 'VENDER'
else:
    señal_hoy = 'ESPERAR'

# ── Salida JSON para la interfaz ──────────────────────────────────────────
resultado = {
    'ticker': ticker,
    'precio_actual': round(precio_actual, 2),
    'señal_hoy': señal_hoy,
    'prob_sube': round(float(prob_hoy[1]), 3),
    'prob_baja': round(float(prob_hoy[0]), 3),
    'capital_modelo': round(capital, 2),
    'capital_bh': round(capital_bh, 2),
    'historial': historial
}

print(json.dumps(resultado))