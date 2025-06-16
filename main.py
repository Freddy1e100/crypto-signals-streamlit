import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from binance.client import Client
import ta
import plotly.graph_objs as go

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"]

def fetch_klines(symbol: str, interval='1h', limit=150):
    client = Client()
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close',
        'volume', 'close_time', 'quote_asset_volume',
        'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def analyze(df):
    df['EMA50'] = ta.trend.ema_indicator(close=df['close'], window=50)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['StochRSI'] = ta.momentum.stochrsi(df['close'], window=14)

    latest = df.iloc[-1]
    signal = 'WAIT'
    if latest['RSI'] < 30 and latest['StochRSI'] < 0.2:
        signal = 'LONG'
    elif latest['RSI'] > 70 and latest['StochRSI'] > 0.8:
        signal = 'SHORT'

    entry_price = latest['close']
    stop_loss = entry_price * (0.97 if signal == 'LONG' else 1.03)
    take_profit = entry_price * (1.05 if signal == 'LONG' else 0.95)

    return signal, entry_price, stop_loss, take_profit

def plot_chart(df, symbol):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['open'],
                                 high=df['high'],
                                 low=df['low'],
                                 close=df['close'],
                                 name='Candles'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], mode='lines', name='EMA50'))
    st.plotly_chart(fig, use_container_width=True)

st.title("📈 Крипто-сигналы (Binance)")
st.write("Получай простые технические сигналы по ключевым парам.")

for pair in PAIRS:
    st.subheader(pair.replace('USDT', '/USDT'))
    try:
        df = fetch_klines(pair)
        df = df.dropna()
        if len(df) < 100:
            st.error("❌ Недостаточно данных")
            continue
        plot_chart(df, pair)
        signal, price, sl, tp = analyze(df)
        st.success(f"✅ Сигнал: **{signal}**")
        st.write(f"⏱️ Время сигнала: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.write(f"💰 Цена входа: {price:.2f}")
        st.write(f"📍 Стоп: {sl:.2f} | Тейк: {tp:.2f}")
    except Exception as e:
        st.error(f"Ошибка: {str(e)}")
