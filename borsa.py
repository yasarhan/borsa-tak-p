import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Sayfa Ayarları
st.set_page_config(layout="wide", page_title="Gemini Master Terminal v13 Web")

# --- ASIL UYGULAMA MANTIĞI: İNDİKATÖR AYARLARI (Sidebar) ---
st.sidebar.title("🔧 İNDİKATÖR AYARLARI")

ema_active = st.sidebar.checkbox("EMA 1 Aktif", value=True)
ema_period = st.sidebar.number_input("EMA 1 Periyot", value=9)

ema2_active = st.sidebar.checkbox("EMA 2 Aktif", value=True)
ema2_period = st.sidebar.number_input("EMA 2 Periyot", value=21)

bb_active = st.sidebar.checkbox("Bollinger Bantları", value=False)
rsi_active = st.sidebar.checkbox("RSI Göster", value=True)

st.sidebar.markdown("---")
# --- TRADE YARDIMCISI KONTROLÜ ---
st.sidebar.subheader("🚀 TRADE YARDIMCISI")
show_signals = st.sidebar.radio("Sinyal Durumu:", ["Sinyalleri Gizle", "Sinyalleri Göster"], index=0)

# --- ANA EKRAN GİRİŞLERİ ---
st.title("Gemini Master Terminal v13.0 (Web)")
c1, c2 = st.columns([3, 1])
with c1:
    hisse = st.text_input("Hisse/Kripto Ara (Örn: THYAO.IS, BTC-USD):", value="THYAO.IS").upper()
with c2:
    zaman = st.selectbox("Zaman Aralığı:", ["3mo", "6mo", "1y", "max"], index=1)

if hisse:
    try:
        df = yf.Ticker(hisse).history(period=zaman)
        
        if not df.empty:
            # Hesaplamalar (Asıl uygulamadaki mantık)
            df['EMA1'] = df['Close'].ewm(span=ema_period).mean()
            df['EMA2'] = df['Close'].ewm(span=ema2_period).mean()
            
            rows = 2 if rsi_active else 1
            fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3] if rsi_active else [1.0])

            # 1. Mum Grafiği
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                         low=df['Low'], close=df['Close'], name="Fiyat"), row=1, col=1)
            
            # EMA Çizgileri
            if ema_active:
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA1'], name=f"EMA {ema_period}"), row=1, col=1)
            if ema2_active:
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA2'], name=f"EMA {ema2_period}"), row=1, col=1)

            # Bollinger
            if bb_active:
                sma = df['Close'].rolling(20).mean()
                std = df['Close'].rolling(20).std()
                fig.add_trace(go.Scatter(x=df.index, y=sma+(std*2), name="BB Üst", line=dict(color='rgba(255,255,255,0.2)')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=sma-(std*2), name="BB Alt", line=dict(color='rgba(255,255,255,0.2)'), fill='tonexty'), row=1, col=1)

            # 2. AL/SAT Sinyalleri (Trade Yardımcısı Mantığı)
            buy = (df['EMA1'] > df['EMA2']) & (df['EMA1'].shift(1) <= df['EMA2'].shift(1))
            sell = (df['EMA1'] < df['EMA2']) & (df['EMA1'].shift(1) >= df['EMA2'].shift(1))
            
            sig_visible = True if show_signals == "Sinyalleri Göster" else "legendonly"
            
            fig.add_trace(go.Scatter(x=df[buy].index, y=df[buy]['Low'] * 0.99, mode='markers', 
                                     marker=dict(symbol='triangle-up', size=15, color='#00ff00'), 
                                     name='AL Sinyali', visible=sig_visible), row=1, col=1)
            fig.add_trace(go.Scatter(x=df[sell].index, y=df[sell]['High'] * 1.01, mode='markers', 
                                     marker=dict(symbol='triangle-down', size=15, color='#ff0000'), 
                                     name='SAT Sinyali', visible=sig_visible), row=1, col=1)

            # RSI Alt Panel
            if rsi_active:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain/loss)))
                fig.add_trace(go.Scatter(x=df.index, y=rsi, name="RSI", line=dict(color='#787b86')), row=2, col=1)

            # Layout Ayarları (Eksen temizleme dahil)
            fig.update_layout(height=800, template="plotly_dark", dragmode="pan", 
                              xaxis_rangeslider_visible=False, margin=dict(t=50))
            fig.update_xaxes(title_text=""); fig.update_yaxes(title_text="")

            # Çizim Araçları Aktif (Editable)
            st.plotly_chart(fig, use_container_width=True, config={
                'scrollZoom': True, 
                'editable': True, 
                'modeBarButtonsToAdd': ['drawline', 'eraseshape', 'addannotation']
            })

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")