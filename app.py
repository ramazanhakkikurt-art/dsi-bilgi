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
        # Excel hiyerarşisini doğrudan okuyoruz
        df = pd.read_excel(excel_yolu, sheet_name=None, header=None)
        sayfalar = list(df.keys())
        
        secilen_sayfa = st.sidebar.selectbox("Görüntülenecek Sayfa/Veri Seti", sayfalar)
        raw_data = df[secilen_sayfa].dropna(how='all')
        
        # Başlık satırını bul
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ|İŞİN ADI').any():
                header_row_idx = idx
                break
                
        columns = raw_data.loc[header_row_idx].astype(str).str.strip().tolist()
        data = raw_data.loc[header_row_idx + 1:].copy()
        data.columns = columns
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        # Sütun dinamiklerini yakala
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
        
        # Toplam satırlarını çift saymamak için ayıkla
        metrik_data = data[~data[s_etiket].astype(str).str.contains('Toplam|TOPLAM|Grand Total', case=False)].copy()
        toplam_satiri = data[data[s_etiket].astype(str).str.contains('Genel Toplam|GENEL TOPLAM', case=False)]
        
        if not toplam_satiri.empty:
            t_basi = temiz_sayi_yap(toplam_satiri[s_basi].values[0])
            t_revize = temiz_sayi_yap(toplam_satiri[s_revize].values[0])
            t_harcama = temiz_sayi_yap(toplam_satiri[s_harcama].values[0])
            t_kalan = t_revize - t_harcama
        else:
            t_basi = metrik_data['Basi_Num'].sum()
            t_revize = metrik_data['Revize_Num'].sum()
            t_harcama = metrik_data['Harcama_Num'].sum()
            t_kalan = t_revize - t_harcama

        m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{tr_format(t_basi)} TL</h3></div>", unsafe_allow_html=True)
        m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{tr_format(t_revize)} TL</h3></div>", unsafe_allow_html=True)
        m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Yılı Harcaması</h4><h3 style='color:#34d399; font-size:20px;'>{tr_format(t_harcama)} TL</h3></div>", unsafe_allow_html=True)
        m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{tr_format(t_kalan)} TL</h3></div>", unsafe_allow_html=True)
        
        # --- İSTEDİĞİN EKSTRA ETKİLEŞİMLİ PİVOT TABLO ALANI ---
        st.subheader("📋 Seçmeli Alt İş Listesi")
        st.info("Aşağıdaki listeden bir ana iş seçtiğinizde, tıpkı Excel'deki gibi altındaki tüm detaylı işler ödenekleriyle sıralanır.")
        
        # Ana sektörleri belirle (büyük harfli olan ve toplam içermeyen satırlar)
        ana_kalemler = data[~data[s_etiket].astype(str).str.contains('Toplam|TOPLAM|Grand Total', case=False)][s_etiket].unique().tolist()
        
        # Listeden sadece ana başlık niteliğindekileri süz
        ana_isler = [x for x in ana_kalemler if x.isupper() or len(x) < 40]
        
        secilen_is = st.selectbox("Tıklamak istediğiniz Ana İş Kalemini Seçin:", ["Tüm Listeyi Düz Göster"] + ana_isler)
        
        # Tabloyu formatla
        display_data = pd.DataFrame()
        display_data[s_etiket] = data[s_etiket].fillna("").astype(str)
        display_data[s_basi] = data['Basi_Num'].apply(tr_format)
        display_data[s_revize] = data['Revize_Num'].apply(tr_format)
        display_data[s_harcama] = data['Harcama_Num'].apply(tr_format)
        display_data[s_kalan] = data['Kalan_Num'].apply(tr_format)
        
        for col in columns:
            if col not in [s_etiket, s_basi, s_revize, s_harcama, s_kalan]:
                display_data[col] = data[col].fillna("").astype(str)
        
        if secilen_is != "Tüm Listeyi Düz Göster":
            # Seçilen ana iş kalemini bul ve Excel'de onun hemen altında yer alan (bir sonraki ana başlığa kadar olan) alt işleri yakala
            idx_list = data.index.tolist()
            start_idx = data[data[s_etiket] == secilen_is].index[0]
            start_pos = idx_list.index(start_idx)
            
            sub_rows = []
            sub_rows.append(display_data.loc[start_idx]) # Ana başlığın kendisi
            
            for p in idx_list[start_pos + 1:]:
                val = str(data.loc[p, s_etiket]).strip()
                # Eğer yeni bir büyük harfli ana başlığa geldiyse veya toplam satırıysa dur
                if val in ana_isler or 'Toplam' in val or 'TOPLAM' in val:
                    break
                sub_rows.append(display_data.loc[p])
                
            filtered_display = pd.DataFrame(sub_rows)
            st.dataframe(filtered_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(display_data, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
