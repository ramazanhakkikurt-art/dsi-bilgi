import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="DSİ 18. Bölge Müdürlüğü Yatırım İzleme Paneli", layout="wide")

st.title("📊 Yatırım İzleme ve Performans Raporlama Programı")
st.write("DSİ 18. Bölge Müdürlüğü Ödenek ve Harcama Durumu Canlı Takip Paneli")

# Excel dosyasını arkada otomatik oku
excel_yolu = "Harcama.xlsx"

if os.path.exists(excel_yolu):
    try:
        df = pd.read_excel(excel_yolu, sheet_name=None)
        sayfalar = list(df.keys())
        
        secilen_sayfa = st.sidebar.selectbox("Görüntülenecek Sayfa/Veri Seti", sayfalar)
        data = df[secilen_sayfa].dropna(how='all')
        data.columns = [str(c).strip() for c in data.columns]
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        if 'SENE BASI ODENEGI' in data.columns and 'REVIZE ODENEK' in data.columns:
            st.subheader("💰 Genel Ödenek ve Harcama Özeti")
            
            toplam_basi = pd.to_numeric(data['SENE BASI ODENEGI'], errors='coerce').sum()
            toplam_revize = pd.to_numeric(data['REVIZE ODENEK'], errors='coerce').sum()
            toplam_harcama = pd.to_numeric(data['YILI HARCAMA'], errors='coerce').sum() if 'YILI HARCAMA' in data.columns else 0
            kalan_odenek = pd.to_numeric(data['YILI ÖDENEĞİ KALAN'], errors='coerce').sum() if 'YILI ÖDENEĞİ KALAN' in data.columns else (toplam_revize - toplam_harcama)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Toplam Sene Başı Ödeneği", f"{toplam_basi:,.2f} TL")
            m2.metric("Toplam Revize Ödenek", f"{toplam_revize:,.2f} TL")
            m3.metric("Toplam Yılı Harcaması", f"{toplam_harcama:,.2f} TL")
            m4.metric("Kalan Ödenek Bakiyesi", f"{kalan_odenek:,.2f} TL")
            
            st.subheader("📈 İş Türlerine Göre Ödenek Dağılımı")
            if 'İŞİN TÜRÜ' in data.columns:
                grafik_data = data.groupby('İŞİN TÜRÜ')['REVIZE ODENEK'].sum().reset_index()
                fig = px.bar(grafik_data, x='İŞİN TÜRÜ', y='REVIZE ODENEK', color='İŞİN TÜRÜ', labels={'REVIZE ODENEK':'Revize Ödenek (TL)'})
                st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🔍 Akıllı İş/Proje Sorgulama")
        arama = st.text_input("Aramak istediğiniz işin adı, yeri veya türünü yazın:")
        if arama:
            mask = data.astype(str).apply(lambda x: x.str.contains(arama, case=False)).any(axis=1)
            st.dataframe(data[mask])
        else:
            st.dataframe(data.head(100))
            
    except Exception as e:
        st.error(f"Veri okunurken hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası bulunamadı. Lütfen GitHub deposuna yükleyin.")
