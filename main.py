import streamlit as st
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
from binance.client import Client
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator, StochRSIIndicator

# Настройки Binance (публичные, без ключа)
client = Client()

# Пары и параметры
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]
SYMBOL_NAMES = {
    "BTCUSDT": "BTC/USDT",
    "ETHUSDT": "ETH/USDT",
    "SOLUSDT": "SOL/USDT",
    "PAXGUSDT": "PAXG/USDT"
}
TIMEFRAME = "1h"
LIMIT = 150

# Заголовок Streamlit
st.title("📈 Крипто-сигналы (Binance)")
st.markdown("Получай простые технические сигналы по ключевым парам.")

# Функция получения исторических данных
def get_binance_data(symbol, interval="1h", limit=150):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base", "Taker Buy Quote", "Ignore"
        ])
        df["Open Time"] = pd.to_datetime(df["Open Time"], unit="ms")
        df.set_index("Open Time", inplace=True)
        df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
        return df
    except Exception as e:
        return None

# Функция анализа и вывода сигналов
def analyze(df, symbol):
    try:
        ema = EMAIndicator(close=df["Close"], window=50)
        df["EMA50"] = ema.ema_indicator()

        rsi = RSIIndicator(close=df["Close"])
        df["RSI"] = rsi.rsi()

        stoch = StochRSIIndicator(close=df["Close"])
        df["StochRSI"] = stoch.stochrsi()

        df.dropna(inplace=True)
        last = df.iloc[-1]

        signal = "⏸️ Нейтрально"
        if last["RSI"] < 30 and last["StochRSI"] < 0.2 and last["Close"] > last["EMA50"]:
            signal = "✅ LONG"
        elif last["RSI"] > 70 and last["StochRSI"] > 0.8 and last["Close"] < last["EMA50"]:
            signal = "🔻 SHORT"

        entry_price = round(last["Close"], 2)
        stop_loss = round(entry_price * (0.97 if signal == "✅ LONG" else 1.03), 2)
        take_profit = round(entry_price * (1.03 if signal == "✅ LONG" else 0.97), 2)

        # График
        fig, ax = plt.subplots(figsize=(6, 3))
        df["Close"].plot(ax=ax, label="Цена")
        df["EMA50"].plot(ax=ax, label="EMA50")
        ax.set_title(f"{SYMBOL_NAMES[symbol]} - Цена и EMA50")
        ax.legend()
        st.pyplot(fig)

        # Сигнал
        st.markdown(f"### {SYMBOL_NAMES[symbol]}")
        st.write(f"{signal}")
        st.write(f"⏱️ Время сигнала: {df.index[-1]}")
        st.write(f"💰 Цена входа: {entry_price}")
        st.write(f"📍 Стоп-лосс: {stop_loss}")
        st.write(f"🎯 Тейк-профит: {take_profit}")

    except Exception as e:
        st.markdown(f"### {SYMBOL_NAMES[symbol]}")
        st.error(f"Ошибка: {e}")

# Основной вывод
for pair in PAIRS:
    df = get_binance_data(pair, interval=TIMEFRAME, limit=LIMIT)
    if df is None or len(df) < 60:
        st.markdown(f"### {SYMBOL_NAMES[pair]}")
        st.error("❌ Недостаточно данных")
    else:
        analyze(df, pair)
