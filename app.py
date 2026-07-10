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
        
        # Sütunları netleştir
        s_tur = columns[0]   # B Sütunu: İŞİN TÜRÜ
        s_adi = columns[1]   # C Sütunu: İŞİN ADI
        s_basi = [c for c in columns if 'SENE BASI' in c or 'SENE BAŞI' in c][0]
        s_revize = [c for c in columns if 'REVIZE' in c or 'REVİZE' in c][0]
        s_harcama = [c for c in columns if 'HARCAMA' in c][0]
        s_kalan = [c for c in columns if 'KALAN' in c or 'ÖDENEĞİ KALAN' in c][0]
        
        # Sayısal alanları temizle
        data['Basi_Num'] = data[s_basi].apply(temiz_sayi_yap)
        data['Revize_Num'] = data[s_revize].apply(temiz_sayi_yap)
        data['Harcama_Num'] = data[s_harcama].apply(temiz_sayi_yap)
        data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
        
        # Excel'deki toplam satırlarını temizle
        saf_veri = data[
            (~data[s_tur].astype(str).str.contains('Toplam|TOPLAM|Genel', case=False, na=False)) & 
            (data[s_tur].fillna("").astype(str).str.strip() != "")
        ].copy()
        
        # --- ÜST ÖZET METRİKLER ---
        st.subheader("💰 Genel Ödenek ve Harcama Özeti")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{saf_veri['Basi_Num'].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{saf_veri['Revize_Num'].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>YILI HARCAMASI</h4><h3 style='color:#34d399; font-size:20px;'>{saf_veri['Harcama_Num'].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{saf_veri['Kalan_Num'].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        
        # --- EXCEL HİYERARŞİ YAPISI ---
        st.subheader("🔍 Hiyerarşik İş ve Proje Grubu Tablosu")
        
        # Mükerrer sütun hatasını engellemek için pivotu doğrudan sayısal sütunlar üzerinden yapıyoruz
        pivot_df = pd.pivot_table(
            saf_veri,
            index=[s_tur, s_adi],
            values=['Basi_Num', 'Revize_Num', 'Harcama_Num', 'Kalan_Num'],
            aggfunc='sum'
        ).reset_index()
        
        # Görüntülenecek dataframe'i oluştur ve sütun isimlerini temizle
        final_df = pd.DataFrame()
        final_df["İŞİN TÜRÜ (ANA GRUP)"] = pivot_df[s_tur].astype(str)
        final_df["İŞİN ADI / ALT PROJE"] = pivot_df[s_adi].astype(str)
        final_df["SENE BAŞI ÖDENEĞİ"] = pivot_df['Basi_Num']
        final_df["REVİZE ÖDENEK"] = pivot_df['Revize_Num']
        final_df["YILI HARCAMASI"] = pivot_df['Harcama_Num']
        final_df["YILI ÖDENEĞİ KALAN"] = pivot_df['Kalan_Num']
        
        # Tabloyu jilet gibi ekrana bas
        st.dataframe(
            final_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "SENE BAŞI ÖDENEĞİ": st.column_config.NumberColumn(format="%.2f TL"),
                "REVİZE ÖDENEK": st.column_config.NumberColumn(format="%.2f TL"),
                "YILI HARCAMASI": st.column_config.NumberColumn(format="%.2f TL"),
                "YILI ÖDENEĞİ KALAN": st.column_config.NumberColumn(format="%.2f TL")
            }
        )
        
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
