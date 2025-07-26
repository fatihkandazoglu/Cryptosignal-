# Bu kod, MACD, RSI ve Bollinger Bands kombinasyonuna dayalı güçlü bir teknik analiz stratejisi kullanır.
# Alış sinyali: MACD hattı sinyal hattını yukarı keser VE RSI < 30 (oversold) VE Fiyat alt Bollinger Band'ın altında.
# Satış sinyali: MACD hattı sinyal hattını aşağı keser VE RSI > 70 (overbought) VE Fiyat üst Bollinger Band'ın üstünde.
# Telegram'a mesaj gönderir - sadece sinyal (değişim) varsa.

import yfinance as yf
import pandas as pd
from ta.trend import MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands
import requests
import os
import time
from datetime import datetime
import pytz  # Türkiye saati için

# Telegram mesaj gönderme fonksiyonu
def send_telegram_message(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID çevre değişkenleri eksik!")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print("Mesaj gönderme hatası:", response.text)
    except Exception as e:
        print("Hata oluştu:", str(e))

# Teknik analiz fonksiyonu
def get_signals(tickers):
    signals = {}
    for ticker in tickers:
        try:
            # Veriyi çek (son 300 gün)
            data = yf.download(ticker, period='300d', interval='1d')
            if data.empty:
                continue
            
            # Veriyi 1 boyutlu hale getir (Close sütununu al)
            close_data = data['Close'].values.flatten()  # Flatten ile 1D emin ol
            
            # İndikatörleri hesapla
            macd = MACD(close=pd.Series(close_data), window_slow=26, window_fast=12, window_sign=9)
            data['MACD'] = macd.macd()
            data['MACD_Signal'] = macd.macd_signal()
            
            rsi = RSIIndicator(close=pd.Series(close_data), window=14)
            data['RSI'] = rsi.rsi()
            
            bb = BollingerBands(close=pd.Series(close_data), window=20, window_dev=2)
            data['BB_High'] = bb.bollinger_hband()
            data['BB_Low'] = bb.bollinger_lband()
            
            # Son değerler
            close = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            
            macd_now = data['MACD'].iloc[-1]
            macd_prev = data['MACD'].iloc[-2]
            macd_signal_now = data['MACD_Signal'].iloc[-1]
            macd_signal_prev = data['MACD_Signal'].iloc[-2]
            
            rsi_now = data['RSI'].iloc[-1]
            
            bb_high = data['BB_High'].iloc[-1]
            bb_low = data['BB_Low'].iloc[-1]
            
            # Alış sinyali (gevşetildi: RSI < 35)
            if (macd_prev <= macd_signal_prev and macd_now > macd_signal_now) and (rsi_now < 35) and (close < bb_low):
                signals[ticker] = f"Alış Sinyali - Fiyat: ${close:.2f}, RSI: {rsi_now:.2f}"
            
            # Satış sinyali (gevşetildi: RSI > 65)
            elif (macd_prev >= macd_signal_prev and macd_now < macd_signal_now) and (rsi_now > 65) and (close > bb_high):
                signals[ticker] = f"Satış Sinyali - Fiyat: ${close:.2f}, RSI: {rsi_now:.2f}"
        
        except Exception as e:
            print(f"{ticker} için hata: {str(e)}")
    
    return signals

# Ana fonksiyon
def main():
    tickers = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'ADA-USD', 'XRP-USD', 'DOGE-USD', 'BNB-USD', 'AVAX-USD', 'LINK-USD', 'DOT-USD']  # Daha fazla coin eklendi: AVAX, LINK, DOT
    signals = get_signals(tickers)
    
    # Türkiye saati ayarı (UTC+3)
    tz_tr = pytz.timezone('Europe/Istanbul')
    current_time = datetime.now(tz_tr).strftime('%Y-%m-%d %H:%M:%S')
    
    if signals:  # Sadece sinyal (değişim) varsa mesaj gönder
        message = f"Teknik Analiz Sinyalleri ({current_time}):\n"
        for ticker, signal in signals.items():
            message += f"{ticker}: {signal}\n"
        send_telegram_message(message)
    # Sinyal yoksa mesaj gönderme - sessiz kal

# GitHub Actions için giriş noktası
if __name__ == "__main__":
    main()  # GitHub Actions'ta tek sefer çalışır, schedule ile periyodik yapılır
