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

# Açık olan sektörleri hafızada tutuyoruz
if 'acik_sektorler' not in st.session_state:
    st.session_state.acik_sektorler = set()

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
            t_kalan = t_revize - t_harcama

        m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{tr_format(t_basi)} TL</h3></div>", unsafe_allow_html=True)
        m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{tr_format(t_revize)} TL</h3></div>", unsafe_allow_html=True)
        m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Yılı Harcaması</h4><h3 style='color:#34d399; font-size:20px;'>{tr_format(t_harcama)} TL</h3></div>", unsafe_allow_html=True)
        m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{tr_format(t_kalan)} TL</h3></div>", unsafe_allow_html=True)
        
        # --- BUTON KONTROLLÜ PİVOT ALANI ---
        st.subheader("📋 Yatırım ve Proje İzleme Paneli")
        
        # Sektör başlıklarını çek
        ana_isler = []
        for x in data[s_etiket].fillna("").astype(str):
            x_temiz = x.strip()
            if x_temiz.isupper() and not any(t in x_temiz for t in ["TOPLAM", "Toplam", "GENEL"]):
                if x_temiz not in ana_isler:
                    ana_isler.append(x_temiz)
        
        # Tablonun üstüne kontrol butonlarını diziyoruz (Yan yana şık butonlar)
        st.write("📂 **Sektör Detaylarını Aç / Kapat:**")
        cols_buttons = st.columns(len(ana_isler))
        
        for idx, sektor in enumerate(ana_isler):
            with cols_buttons[idx]:
                # Sektörün durumuna göre buton ismi belirle
                durum = "🔴 Kapat" if sektor in st.session_state.acik_sektorler else "🟢 Aç"
                if st.button(f"{sektor}\n({durum})", key=f"btn_{idx}"):
                    if sektor in st.session_state.acik_sektorler:
                        st.session_state.acik_sektorler.remove(sektor)
                    else:
                        st.session_state.acik_sektorler.add(sektor)
                    st.rerun()
        
        # Dinamik satırları oluşturma
        final_rows = []
        for idx, row in data.iterrows():
            val = str(row[s_etiket]).strip()
            
            if val in ana_isler:
                durum_isareti = "▼" if val in st.session_state.acik_sektorler else "►"
                yeni_satir = row.copy()
                yeni_satir[s_etiket] = f"{durum_isareti} {val}"
                final_rows.append(yeni_satir)
                
                # Eğer butonla açıldıysa alt projeleri ekle
                if val in st.session_state.acik_sektorler:
                    idx_list = data.index.tolist()
                    start_pos = idx_list.index(idx)
                    
                    for p in idx_list[start_pos + 1:]:
                        sub_val = str(data.loc[p, s_etiket]).strip()
                        if sub_val in ana_isler or "Toplam" in sub_val or "TOPLAM" in sub_val:
                            break
                        
                        sub_row = data.loc[p].copy()
                        sub_row[s_etiket] = f"        └── {sub_val}"
                        final_rows.append(sub_row)
                        
            elif "Toplam" in val or "TOPLAM" in val:
                final_rows.append(row)
                
        # Tabloyu bas
        if final_rows:
            display_df = pd.DataFrame(final_rows)
            final_display = pd.DataFrame()
            final_display["İŞİN ADI / SEKTÖRÜ"] = display_df[s_etiket]
            final_display[s_basi] = display_df['Basi_Num'].apply(tr_format)
            final_display[s_revize] = display_df['Revize_Num'].apply(tr_format)
            final_display[s_harcama] = display_df['Harcama_Num'].apply(tr_format)
            final_display[s_kalan] = display_df['Kalan_Num'].apply(tr_format)
            
            for col in columns:
                if col not in [s_etiket, s_basi, s_revize, s_harcama, s_kalan]:
                    final_display[col] = display_df[col].fillna("").astype(str)
                    
            st.dataframe(final_display, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
