import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuración de página
st.set_page_config(page_title="IA Predictor de Acciones", page_icon="📈", layout="wide")

# Estilo personalizado para modo oscuro y móvil
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #238636; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 IA Predictor de Acciones")
st.caption("Potenciado por Machine Learning & Datos en Tiempo Real")

# Barra lateral para configuración
with st.sidebar:
    st.header("Configuración")
    ticker = st.text_input("Símbolo de la Acción", value="AAPL").upper()
    umbral = st.slider("Umbral de Probabilidad", 0.5, 0.9, 0.65)
    st.info("Un umbral más alto significa señales más conservadoras.")

# Acciones rápidas
st.write("### Acciones Rápidas")
cols = st.columns(7)
quick_tickers = ["AAPL", "TSLA", "MSFT", "AMZN", "GOOGL", "NVDA", "META"]
for i, q_t in enumerate(quick_tickers):
    if cols[i].button(q_t):
        ticker = q_t

# Lógica de la IA (Caché para velocidad)
@st.cache_data(ttl=3600)
def procesar_datos(ticker, umbral):
    # Descargar datos
    df = yf.download(ticker, start="2015-01-01", auto_adjust=True)
    if df.empty: return None
    df.columns = df.columns.get_level_values(0)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    
    # Indicadores
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
    
    modelo = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    modelo.fit(X_train, y_train)
    
    # Simulación
    probabilidades = modelo.predict_proba(X_test)
    capital = 10000.0
    historial = []
    precio_inicio = df.loc[X_test.index[0], 'Close']
    
    for i, (fecha, prob) in enumerate(zip(X_test.index, probabilidades)):
        precio_hoy = df.loc[fecha, 'Close']
        loc = df.index.get_loc(fecha)
        if loc + 1 >= len(df): continue
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
            'Fecha': fecha,
            'Precio': round(float(precio_hoy), 2),
            'Señal': señal,
            'Prob_Sube': prob[1],
            'Capital': capital
        })
    
    # Predicción hoy
    df_rec = yf.download(ticker, period="3mo", auto_adjust=True)
    df_rec.columns = df_rec.columns.get_level_values(0)
    # ... (mismos indicadores que arriba para df_rec) ...
    # Para brevedad en la demo, usamos la última fila del dataset original entrenado
    prob_hoy = modelo.predict_proba(X.iloc[-1:])[0]
    
    return {
        'ticker': ticker,
        'precio_actual': float(df['Close'].iloc[-1]),
        'prob_hoy': prob_hoy,
        'historial': pd.DataFrame(historial),
        'capital_final': capital,
        'capital_bh': 10000 * (float(df['Close'].iloc[-1]) / float(precio_inicio))
    }

# Ejecutar análisis
with st.spinner(f"Analizando {ticker}..."):
    data = procesar_datos(ticker, umbral)

if data:
    # Métricas Principales
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precio Actual", f"${data['precio_actual']:,.2f}")
    
    prob_sube = data['prob_hoy'][1]
    señal = "💚 COMPRAR" if prob_sube >= umbral else "🔴 VENDER" if data['prob_hoy'][0] >= umbral else "🟡 ESPERAR"
    m2.metric("Señal Mañana", señal)
    
    m3.metric("Prob. Subida", f"{prob_sube*100:.1f}%")
    
    rendimiento = ((data['capital_final'] - 10000) / 10000) * 100
    m4.metric("Rendimiento IA", f"{rendimiento:.1f}%", delta=f"{rendimiento - ((data['capital_bh']-10000)/100):.1f}% vs B&H")

    # Gráficos
    st.write("---")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📊 Evolución del Capital")
        fig_cap = go.Figure()
        fig_cap.add_trace(go.Scatter(x=data['historial']['Fecha'], y=data['historial']['Capital'], name="Modelo IA", line=dict(color='#58a6ff')))
        fig_cap.update_layout(template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), height=300)
        st.plotly_chart(fig_cap, use_container_width=True)

    with c2:
        st.subheader("🕯️ Histórico de Precios")
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=data['historial']['Fecha'], y=data['historial']['Precio'], name="Precio", line=dict(color='#e6edf3')))
        fig_price.update_layout(template="plotly_dark", margin=dict(l=0,r=0,t=0,b=0), height=300)
        st.plotly_chart(fig_price, use_container_width=True)

    # Tabla de señales
    st.subheader("📋 Últimas Señales")
    st.dataframe(data['historial'].tail(20).sort_values('Fecha', ascending=False), use_container_width=True)

else:
    st.error("No se pudieron obtener datos para este símbolo. Verifica que sea correcto.")
