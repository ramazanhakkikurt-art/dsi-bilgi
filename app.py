import streamlit as st
import pandas as pd
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
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ|İŞİN ADI').any():
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
        
        toplam_satiri = data[data[s_etiket].astype(str).str.contains('Genel Toplam|GENEL TOPLAM', case=False)]
        metrik_data = data[~data[s_etiket].astype(str).str.contains('Toplam|TOPLAM|Grand Total', case=False)].copy()
        
        if not toplam_satiri.empty:
            t_basi = temiz_sayi_yap(toplam_satiri[s_basi].values[0])
            t_revize = temiz_sayi_yap(toplam_satiri[s_revize].values[0])
            t_harcama = temiz_sayi_yap(toplam_satiri[s_harcama].values[0])
            t_kalan = t_revize - t_harcama
        else:
            t_basi = metrik_data['Basi_Num'].sum()
            t_revize = metrik_data['Revize_Num'].sum()
            t_harcama = metrik_data['Harcama_Num'].sum()
            t_kalan = t_rev
