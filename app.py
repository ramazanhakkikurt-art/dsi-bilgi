import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="DSİ 18. Bölge Müdürlüğü Yatırım İzleme Paneli", layout="wide")

st.title("📊 Yatırım İzleme ve Performans Raporlama Programı")
st.write("DSİ 18. Bölge Müdürlüğü Ödenek ve Harcama Durumu Canlı Takip Paneli")

excel_yolu = "Harcama.xlsx"

# Sayı temizleme fonksiyonu (Nokta ve virgül karmaşasını çözer)
def temiz_sayi_yap(val):
    if pd.isna(val) or str(val).strip().lower() in ['none', 'nan', '']:
        return 0.0
    try:
        s = str(val).strip()
        # Eğer hücre formatı zaten sayısal geldiyse direkt çevir
        return float(s)
    except:
        try:
            s = str(val).strip()
            # 1.234.567,89 veya 1234567.89 formatlarını güvenli temizle
            if ',' in s and '.' in s:
                s = s.replace('.', '').replace(',', '.')
            elif ',' in s:
                s = s.replace(',', '.')
            return float(s)
        except:
            return 0.0

# Türkiye formatına (1.234.567,89) çeviren fonksiyon
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
        
        # Başlık satırını bul
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ').any():
                header_row_idx = idx
                break
                
        columns = raw_data.loc[header_row_idx].astype(str).str.strip().tolist()
        data = raw_data.loc[header_row_idx + 1:].copy()
        data.columns = columns
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        # --- MATEMATİKSEL TEMİZLİK VE HESAPLAMA ---
        # Sütun isimlerini netleştiriyoruz
        s_etiket = columns[0]
        s_basi = [c for c in columns if 'SENE BASI' in c or 'SENE BAŞI' in c][0]
        s_revize = [c for c in columns if 'REVIZE' in c or 'REVİZE' in c][0]
        s_harcama = [c for c in columns if 'HARCAMA' in c][0]
        s_kalan = [c for c in columns if 'KALAN' in c or 'ÖDENEĞİ KALAN' in c][0]
        
        # Temiz sayısal sütunlar oluştur
        data['Basi_Num'] = data[s_basi].apply(temiz_sayi_yap)
        data['Revize_Num'] = data[s_revize].apply(temiz_sayi_yap)
        data['Harcama_Num'] = data[s_harcama].apply(temiz_sayi_yap)
        
        # Kalan ödeneği hata payı bırakmamak için biz hesaplıyoruz (Revize - Harcama)
        data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
        
        # --- ÜST METRİKLER ---
        st.subheader("💰 Genel Ödenek ve Harcama Özeti")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Toplam Sene Başı Ödeneği", f"{tr_format(data['Basi_Num'].sum())} TL")
        m2.metric("Toplam Revize Ödenek", f"{tr_format(data['Revize_Num'].sum())} TL")
        m3.metric("Toplam Yılı Harcaması", f"{tr_format(data['Harcama_Num'].sum())} TL")
        m4.metric("Kalan Ödenek Bakiyesi", f"{tr_format(data['Kalan_Num'].sum())} TL")
        
        # --- EKRANA BASILACAK TABLOYU FORMATLA ---
        display_data = pd.DataFrame()
        display_data[s_etiket] = data[s_etiket].fillna("").astype(str)
        display_data[s_basi] = data['Basi_Num'].apply(tr_format)
        display_data[s_revize] = data['Revize_Num'].apply(tr_format)
        display_data[s_harcama] = data['Harcama_Num'].apply(tr_format)
        display_data[s_kalan] = data['Kalan_Num'].apply(tr_format)
        
        # Performans veya diğer sütunlar varsa onları da ekle
        for col in columns:
            if col not in [s_etiket, s_basi, s_revize, s_harcama, s_kalan]:
                display_data[col] = data[col].fillna("").astype(str)
        
        # --- TABLOYU GÖSTER ---
        st.subheader("🔍 Akıllı İş/Proje Sorgulama")
        arama = st.text_input("Aramak istediğiniz işin adı, yeri veya türünü yazın:")
        
        if arama:
            mask = display_data.apply(lambda x: x.astype(str).str.contains(arama, case=False)).any(axis=1)
            st.dataframe(display_data[mask], use_container_width=True, hide_index=True)
        else:
            st.dataframe(display_data, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
