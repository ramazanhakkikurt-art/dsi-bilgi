import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="DSİ 18. Bölge Müdürlüğü Yatırım İzleme Paneli", layout="wide")

st.title("📊 Yatırım İzleme ve Performans Raporlama Programı")
st.write("DSİ 18. Bölge Müdürlüğü Ödenek ve Harcama Durumu Canlı Takip Paneli")

excel_yolu = "Harcama.xlsx"

# Sayıları Türkiye formatına (1.234.567,89) çeviren fonksiyon
def tr_format_str(val):
    if pd.isna(val) or str(val).strip().lower() in ['none', 'nan', '']:
        return ""
    try:
        # Önce sayıya çevir, sonra formatla
        num = float(str(val).replace('.', '').replace(',', '.').strip())
        return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(val)

if os.path.exists(excel_yolu):
    try:
        # Excel'i doğrudan oku
        df = pd.read_excel(excel_yolu, sheet_name=None, header=None)
        sayfalar = list(df.keys())
        
        secilen_sayfa = st.sidebar.selectbox("Görüntülenecek Sayfa/Veri Seti", sayfalar)
        raw_data = df[secilen_sayfa].dropna(how='all')
        
        # --- BAŞLIKLARI DÜZELTME (Unnamed sorununu çözer) ---
        # "Satır Etiketleri" yazan satırı bulup başlık yapıyoruz
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ').any():
                header_row_idx = idx
                break
                
        # Başlık satırını ayarla ve altındaki veriyi al
        columns = raw_data.loc[header_row_idx].astype(str).str.strip().tolist()
        data = raw_data.loc[header_row_idx + 1:].copy()
        data.columns = columns
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        # --- FORMATLAMA İŞLEMİ ---
        display_data = data.copy()
        formatlanacak_sutunlar = [c for c in display_data.columns if 'ODENEG' in c or 'ODENEK' in c or 'HARCAMA' in c or 'KALAN' in c]
        
        for col in display_data.columns:
            if col in formatlanacak_sutunlar:
                display_data[col] = display_data[col].apply(tr_format_str)
            else:
                display_data[col] = display_data[col].fillna("").astype(str)
        
        # --- TABLOYU BAS ---
        st.subheader("🔍 Akıllı İş/Proje Sorgulama")
        arama = st.text_input("Aramak istediğiniz işin adı, yeri veya türünü yazın:")
        
        if arama:
            mask = display_data.apply(lambda x: x.astype(str).str.contains(arama, case=False)).any(axis=1)
            st.dataframe(display_data[mask], use_container_width=True)
        else:
            st.dataframe(display_data, use_container_width=True)
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
