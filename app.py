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
        data[s_basi] = data[s_basi].apply(temiz_sayi_yap)
        data[s_revize] = data[s_revize].apply(temiz_sayi_yap)
        data[s_harcama] = data[s_harcama].apply(temiz_sayi_yap)
        data[s_kalan] = data[s_revize] - data[s_harcama]
        
        # Excel'deki toplam ve alt satır karmaşasını temizle, saf veriyi çek
        saf_veri = data[
            (~data[s_tur].astype(str).str.contains('Toplam|TOPLAM|Genel', case=False, na=False)) & 
            (data[s_tur].fillna("").astype(str).str.strip() != "")
        ].copy()
        
        # --- ÜST ÖZET METRİKLER ---
        st.subheader("💰 Genel Ödenek ve Harcama Özeti")
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{saf_veri[s_basi].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{saf_veri[s_revize].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Yılı Harcaması</h4><h3 style='color:#34d399; font-size:20px;'>{saf_veri[s_harcama].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{saf_veri[s_kalan].sum():,.2f} TL</h3></div>", unsafe_allow_html=True)
        
        # --- TAM İSTEDİĞİN EXCEL GRUPLANDIRMA YAPISI ---
        st.subheader("🔍 Hiyerarşik İş ve Proje Grubu Tablosu")
        st.info("Sol taraftaki hiyerarşik grup yapısı sayesinde verileri doğrudan Excel düzeninde inceleyebilirsiniz.")
        
        # Pandas Pivot kullanarak B ve C sütununu tam senin ekran görüntündeki gibi iç içe bağlıyoruz
        pivot_df = pd.pivot_table(
            saf_veri,
            index=[s_tur, s_adi], # Önce İşin Türü, altında İşin Adı sıralanır
            values=[s_basi, s_revize, s_harcama, s_kalan],
            aggfunc='sum'
        ).reset_index()
        
        # Sütunları müdürün alışık olduğu orijinal sıraya diziyoruz
        pivot_df = pivot_df[[s_tur, s_adi, s_basi, s_revize, s_harcama, s_kalan]]
        
        # Streamlit'in akıllı veri tablosu yapılandırması (Sayıları doğrudan para birimi yapar)
        st.dataframe(
            pivot_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                s_tur: st.column_config.TextColumn("İŞİN TÜRÜ (ANA GRUP)"),
                s_adi: st.column_config.TextColumn("İŞİN ADI / ALT PROJE"),
                s_basi: st.column_config.NumberColumn("SENE BAŞI ÖDENEĞİ", format="%.2f TL"),
                s_revize: st.column_config.NumberColumn("REVİZE ÖDENEK", format="%.2f TL"),
                s_harcama: st.column_config.NumberColumn("YILI HARCAMASI", format="%.2f TL"),
                s_kalan: st.column_config.NumberColumn("YILI ÖDENEĞİ KALAN", format="%.2f TL")
            }
        )
        
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
