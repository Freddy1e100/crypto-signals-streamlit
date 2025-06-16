import streamlit as st import pandas as pd import matplotlib.pyplot as plt import ta import datetime import os import telegram from io import BytesIO from binance.client import Client from dotenv import load_dotenv

load_dotenv()

Binance API (используем публичный доступ без ключей)

client = Client()

Telegram настройки

BOT_TOKEN = os.getenv("TOKEN") or "7903391510:AAFgkj03oD8CGL3hfVNKPAE64phffpsxAEM" CHAT_ID = int(os.getenv("CHAT_ID") or 646839309) bot = telegram.Bot(token=BOT_TOKEN)

def send_signal_to_telegram(fig, text): buffer = BytesIO() fig.savefig(buffer, format='PNG') buffer.seek(0) bot.send_photo(chat_id=CHAT_ID, photo=buffer, caption=text)

def fetch_klines(symbol, interval='1h', limit=100): try: klines = client.get_klines(symbol=symbol, interval=interval, limit=limit) df = pd.DataFrame(klines, columns=[ 'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time', 'Quote_asset_volume', 'Number_of_trades', 'Taker_buy_base_volume', 'Taker_buy_quote_volume', 'Ignore'])

df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df.astype(float)
    return df[['Open', 'High', 'Low', 'Close', 'Volume']]
except Exception as e:
    return None

def analyze(df): try: df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50).ema_indicator() df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi() stoch = ta.momentum.StochRSIIndicator(df['Close']) df['StochRSI'] = stoch.stochrsi()

latest = df.iloc[-1]
    signal = None

    if latest['Close'] > latest['EMA50'] and latest['RSI'] > 50 and latest['StochRSI'] > 0.8:
        signal = 'LONG'
    elif latest['Close'] < latest['EMA50'] and latest['RSI'] < 50 and latest['StochRSI'] < 0.2:
        signal = 'SHORT'

    if signal:
        fig, ax = plt.subplots()
        df[['Close', 'EMA50']].tail(50).plot(ax=ax)
        ax.set_title(signal)

        entry_price = round(latest['Close'], 2)
        stop_loss = round(entry_price * (0.98 if signal == 'LONG' else 1.02), 2)
        take_profit = round(entry_price * (1.04 if signal == 'LONG' else 0.96), 2)

        text = (
            f"📈 Сигнал по паре

" f"{signal}\n" f"⏱️ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n" f"💰 Цена входа: {entry_price}\n" f"📍 Стоп: {stop_loss}\n" f"🎯 Тейк: {take_profit}" ) send_signal_to_telegram(fig, text) return signal, text else: return None, "❌ Недостаточно условий для сигнала" except Exception as e: return None, f"Ошибка: {str(e)}"

Streamlit UI

st.title("📈 Крипто-сигналы (Binance)") st.markdown("Получай простые технические сигналы по ключевым парам.")

pairs = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "PAXGUSDT"] for pair in pairs: st.subheader(f"### {pair.replace('USDT', '/USDT')}") df = fetch_klines(pair) if df is not None: signal, message = analyze(df) st.write(message) else: st.write("❌ Недостаточно данных")

