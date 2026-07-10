import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="DSİ 18. Bölge Müdürlüğü Yatırım İzleme Paneli", layout="wide")

st.title("📊 Yatırım İzleme ve Performans Raporlama Programı")
st.write("DSİ 18. Bölge Müdürlüğü Ödenek ve Harcama Durumu Canlı Takip Paneli")

excel_yolu = "Harcama.xlsx"

def temiz_sayi_yap(val):
    if pd.isna(val) or str(val).strip().lower() in ['none', 'nan', '']:
        return 0.0
    try:
        return float(str(val).strip())
    except:
        try:
            s = str(val).strip()
            if ',' in s and '.' in s:
                s = s.replace('.', '').replace(',', '.')
            elif ',' in s:
                s = s.replace(',', '.')
            return float(s)
        except:
            return 0.0

def tr_format(val):
    try:
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

if os.path.exists(excel_yolu):
    try:
        df = pd.read_excel(excel_yolu, sheet_name=None, header=None)
        sayfalar = list(df.keys())
        
        secilen_sayfa = st.sidebar.selectbox("Görüntülenecek Sayfa/Veri Seti", sayfalar)
        raw_data = df[secilen_sayfa].dropna(how='all')
        
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ').any():
                header_row_idx = idx
                break
                
        columns = raw_data.loc[header_row_idx].astype(str).str.strip().tolist()
        data = raw_data.loc[header_row_idx + 1:].copy()
        data.columns = columns
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        s_etiket = columns[0]
        s_basi = [c for c in columns if 'SENE BASI' in c or 'SENE BAŞI' in c][0]
        s_revize = [c for c in columns if 'REVIZE' in c or 'REVİZE' in c][0]
        s_harcama = [c for c in columns if 'HARCAMA' in c][0]
        s_kalan = [c for c in columns if 'KALAN' in c or 'ÖDENEĞİ KALAN' in c][0]
        
        data['Basi_Num'] = data[s_basi].apply(temiz_sayi_yap)
        data['Revize_Num'] = data[s_revize].apply(temiz_sayi_yap)
        data['Harcama_Num'] = data[s_harcama].apply(temiz_sayi_yap)
        data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
        
        # --- ÖZET METRİKLER ---
        st.subheader("💰 Genel Ödenek ve Harcama Özeti")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{tr_format(data['Basi_Num'].sum())} TL</h3></div>", unsafe_allow_html=True)
        m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{tr_format(data['Revize_Num'].sum())} TL</h3></div>", unsafe_allow_html=True)
        m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Yılı Harcaması</h4><h3 style='color:#34d399; font-size:20px;'>{tr_format(data['Harcama_Num'].sum())} TL</h3></div>", unsafe_allow_html=True)
        m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{tr_format(data['Kalan_Num'].sum())} TL</h3></div>", unsafe_allow_html=True)
        
        # --- TEMİZ PASTA GRAFİĞİ ---
        st.subheader("🍕 Sektörlere Göre Bütçe Dağılımı")
        
        grafik_data = data[~data[s_etiket].astype(str).str.contains('Toplam|TOPLAM|Grand Total', case=False)].copy()
        
        if not grafik_data.empty:
            # %2'den küçük olan küçük dilimleri "Diğer" altında toplayarak karmaşayı bitiriyoruz
            toplam_revize = grafik_data['Revize_Num'].sum()
            grafik_data['Yuzde'] = (grafik_data['Revize_Num'] / toplam_revize) * 100
            
            ana_sektorler = grafik_data[grafik_data['Yuzde'] >= 2.0].copy()
            kucuk_sektorler = grafik_data[grafik_data['Yuzde'] < 2.0]
            
            if not kucuk_sektorler.empty:
                diger_satir = pd.DataFrame([{
                    s_etiket: 'DİĞER KÜÇÜK SEKTÖRLER',
                    'Revize_Num': kucuk_sektorler['Revize_Num'].sum()
                }])
                grafik_data_final = pd.concat([ana_sektorler, diger_satir], ignore_index=True)
            else:
                grafik_data_final = ana_sektorler
            
            fig = px.pie(
                grafik_data_final, 
                names=s_etiket, 
                values='Revize_Num',
                hole=0.4
            )
            
            # CRITICAL CHANGE: Yazıları kaldırdık, sadece fareyle üstüne gelince (hover) detaylar gözükecek
            fig.update_traces(
                textinfo='none', 
                hovertemplate="<b>%{label}</b><br>Ödenek: %{value:,.2f} TL<br>Pay: %{percent}<extra></extra>"
            )
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig, use_container_width=True)
        
        # --- TABLO ALANI ---
        st.subheader("🔍 Akıllı İş/Proje Sorgulama")
        display_data = pd.DataFrame()
        display_data[s_etiket] = data[s_etiket].fillna("").astype(str)
        display_data[s_basi] = data['Basi_Num'].apply(tr_format)
        display_data[s_revize] = data['Revize_Num'].apply(tr_format)
        display_data[s_harcama] = data['Harcama_Num'].apply(tr_format)
        display_data[s_kalan] = data['Kalan_Num'].apply(tr_format)
        
        for col in columns:
            if col not in [s_etiket, s_basi, s_revize, s_harcama, s_kalan]:
                display_data[col] = data[col].fillna("").astype(str)
                
        arama = st.text_input("
