import streamlit as st import pandas as pd import datetime import plotly.graph_objects as go from binance.client import Client from ta.momentum import RSIIndicator, StochRSIIndicator from ta.trend import EMAIndicator

Binance client (без ключей, только публичные данные)

client = Client()

Настройки

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"] INTERVAL = Client.KLINE_INTERVAL_1H LIMIT = 100

st.set_page_config(page_title="Крипто-сигналы", layout="wide") st.title("📈 Крипто-сигналы (Binance)") st.markdown("Получай простые технические сигналы по ключевым парам.")

Функция получения и анализа данных

def analyze_symbol(symbol): klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=LIMIT) df = pd.DataFrame(klines, columns=["timestamp", "o", "h", "l", "c", "v", "C", "Q", "n", "TakerBaseVol", "TakerQuoteVol", "Ignore"]) df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms") df.set_index("timestamp", inplace=True) df = df[["o", "h", "l", "c"]].astype(float) df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close"}, inplace=True)

if df.empty or len(df) < 50:
    return None, "❌ Недостаточно данных", None

df["EMA50"] = EMAIndicator(df["Close"], window=50).ema_indicator()
df["RSI"] = RSIIndicator(df["Close"]).rsi()
df["StochRSI"] = StochRSIIndicator(df["Close"]).stochrsi()

last = df.iloc[-1]
price = round(last["Close"], 2)
now = df.index[-1].strftime("%Y-%m-%d %H:%M")

# Сигналы
if last["Close"] > last["EMA50"] and last["RSI"] > 50 and last["StochRSI"] > 0.8:
    signal = "✅ LONG"
elif last["Close"] < last["EMA50"] and last["RSI"] < 50 and last["StochRSI"] < 0.2:
    signal = "🔻 SHORT"
else:
    signal = "➖ Нет сигнала"

# Уровни
stop = round(price * 0.98, 2)
take = round(price * 1.04, 2) if "LONG" in signal else round(price * 0.96, 2)

# График
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df.Open, high=df.High, low=df.Low, close=df.Close, name="Цена"))
fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], line=dict(color="orange"), name="EMA50"))
fig.update_layout(margin=dict(t=20, b=0), height=400, showlegend=True)

info = f"{signal}\n⏱ {now}\n💰 Цена входа: {price}\n📍 Стоп: {stop}\n📍 Тейк: {take}"
return fig, info, df

Отображение

for symbol in PAIRS: st.subheader(symbol.replace("USDT", "/USDT")) fig, info, df = analyze_symbol(symbol) if df is None: st.warning(info) else: st.plotly_chart(fig, use_container_width=True) st.text(info)

