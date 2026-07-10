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

# Hangi ana iş türlerinin (sektörlerin) açık olduğunu hafızada tutmak için session_state
if 'acik_turler' not in st.session_state:
    st.session_state.acik_turler = set()

if os.path.exists(excel_yolu):
    try:
        df = pd.read_excel(excel_yolu, sheet_name=None, header=None)
        sayfalar = list(df.keys())
        
        secilen_sayfa = st.sidebar.selectbox("Görüntülenecek Sayfa/Veri Seti", sayfalar)
        raw_data = df[secilen_sayfa].dropna(how='all')
        
        # Dinamik başlık satırı bulma
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ|İŞİN ADI|PROJE NO').any():
                header_row_idx = idx
                break
                
        columns = raw_data.loc[header_row_idx].astype(str).str.strip().tolist()
        data = raw_data.loc[header_row_idx + 1:].copy()
        data.columns = columns
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        # --- VERİ SEKLESİ İÇİN ÖZEL PIVOT VE GRUPLAMA MANTIĞI ---
        if secilen_sayfa.lower() == "veri" or "veri" in secilen_sayfa.lower():
            
            # Sütun isimlerini tespit et
            col_tur = [c for c in columns if 'TÜRÜ' in c or 'TURU' in c][0]
            col_adi = [c for c in columns if 'ADI' in c or 'is_adi' in c or 'İŞ' in c][1] if len([c for c in columns if 'ADI' in c]) > 1 else [c for c in columns if 'ADI' in c or 'İŞ' in c][0]
            col_basi = [c for c in columns if 'SENE' in c or 'BAŞI' in c or 'BASI' in c][0]
            col_revize = [c for c in columns if 'REVİZE' in c or 'REVIZE' in c][0]
            col_harcama = [c for c in columns if 'HARCAMA' in c or 'YILI' in c][0]
            
            # Sayısal dönüşümler
            data['Basi_Num'] = data[col_basi].apply(temiz_sayi_yap)
            data['Revize_Num'] = data[col_revize].apply(temiz_sayi_yap)
            data['Harcama_Num'] = data[col_harcama].apply(temiz_sayi_yap)
            data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
            
            # Toplamları hesapla (Metrikler için)
            t_basi = data['Basi_Num'].sum()
            t_revize = data['Revize_Num'].sum()
            t_harcama = data['Harcama_Num'].sum()
            t_kalan = t_revize - t_harcama
            
            # --- METRİKLER ---
            st.subheader("💰 Genel Ödenek ve Harcama Özeti")
            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{tr_format(t_basi)} TL</h3></div>", unsafe_allow_html=True)
            m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{tr_format(t_revize)} TL</h3></div>", unsafe_allow_html=True)
            m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Yılı Harcaması</h4><h3 style='color:#34d399; font-size:20px;'>{tr_format(t_harcama)} TL</h3></div>", unsafe_allow_html=True)
            m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{tr_format(t_kalan)} TL</h3></div>", unsafe_allow_html=True)
            
            # --- TAM İSTEDİĞİN TABLO İÇİ GRUPLAMA ALANI ---
            st.subheader("📋 Orijinal Hiyerarşik Yatırım Tablosu")
            
            # Benzersiz iş türlerini (Sektörleri) al
            is_turleri = data[col_tur].dropna().unique().tolist()
            
            # Tabloyu basmak için satır satır hiyerarşik liste oluşturuyoruz
            final_rows = []
            
            for tur in is_turleri:
                tur_filtre = data[data[col_tur] == tur]
                
                # Sektörün toplam bütçelerini hesapla
                s_basi = tur_filtre['Basi_Num'].sum()
                s_revize = tur_filtre['Revize_Num'].sum()
                s_harcama = tur_filtre['Harcama_Num'].sum()
                s_kalan = s_revize - s_harcama
                
                # Açık/Kapalı durum işareti
                durum_isareti = "▼" if tur in st.session_state.acik_turler else "►"
                
                # Ana Sektör Satırı
                final_rows.append({
                    "İŞİN ADI / GRUBU": f"{durum_isareti} {tur}",
                    "SENE BAŞI ÖDENEĞİ": tr_format(s_basi),
                    "REVİZE ÖDENEK": tr_format(s_revize),
                    "YILI HARCAMASI": tr_format(s_harcama),
                    "YILI ÖDENEĞİ KALAN": tr_format(s_kalan),
                    "is_ana_baslik": True,
                    "orj_tur_adi": tur
                })
                
                # Eğer müdür bu sektörü açtıysa, altındaki işleri altına listele
                if tur in st.session_state.acik_turler:
                    for _, sub_row in tur_filtre.iterrows():
                        final_rows.append({
                            "İŞİN ADI / GRUBU": f"    └── {sub_row[col_adi]}",
                            "SENE BAŞI ÖDENEĞİ": tr_format(sub_row['Basi_Num']),
                            "REVİZE ÖDENEK": tr_format(sub_row['Revize_Num']),
                            "YILI HARCAMASI": tr_format(sub_row['Harcama_Num']),
                            "YILI ÖDENEĞİ KALAN": tr_format(sub_row['Kalan_Num']),
                            "is_ana_baslik": False,
                            "orj_tur_adi": tur
                        })
            
            # Genel Toplam Satırını Ekle
            final_rows.append({
                "İŞİN ADI / GRUBU": "📊 GENEL TOPLAM",
                "SENE BAŞI ÖDENEĞİ": tr_format(t_basi),
                "REVİZE ÖDENEK": tr_format(t_revize),
                "YILI HARCAMASI": tr_format(t_harcama),
                "YILI ÖDENEĞİ KALAN": tr_format(t_kalan),
                "is_ana_baslik": False,
                "orj_tur_adi": "TOTAL"
            })
            
            table_df = pd.DataFrame(final_rows)
            
            # --- DOĞRUDAN TABLODAN SEÇİLEN SATIRA GÖRE AÇMA MANTIĞI ---
            # Müdür ana tablodaki satıra tıklayarak altını açıp kapatabilir
            secilen_index = st.selectbox(
                "Detayını açmak veya kapatmak istediğiniz Ana İş Grubunu seçin:",
                options=["Seçim Yapın..."] + is_turleri
            )
            
            if secilen_index != "Seçim Yapın...":
                if secilen_index in st.session_state.acik_turler:
                    st.session_state.acik_turler.remove(secilen_index)
                else:
                    st.session_state.acik_turler.add(secilen_index)
                st.rerun()
            
            # Tabloyu ekrana düz kurumsal yapıda basıyoruz
            st.dataframe(
                table_df[["İŞİN ADI / GRUBU", "SENE BAŞI ÖDENEĞİ", "REVİZE ÖDENEK", "YILI HARCAMASI", "YILI ÖDENEĞİ KALAN"]],
                use_container_width=True,
                hide_index=True
            )
            
        # Diğer düz sekmeler seçilirse bozmadan eski stabil haliyle göster
        else:
            s_etiket = columns[0]
            s_basi = [c for c in columns if 'SENE BASI' in c or 'SENE BAŞI' in c][0]
            s_revize = [c for c in columns if 'REVIZE' in c or 'REVİZE' in c][0]
            s_harcama = [c for c in columns if 'HARCAMA' in c][0]
            s_kalan = [c for c in columns if 'KALAN' in c or 'ÖDENEĞİ KALAN' in c][0]
            
            data['Basi_Num'] = data[s_basi].apply(temiz_sayi_yap)
            data['Revize_Num'] = data[s_revize].apply(temiz_sayi_yap)
            data['Harcama_Num'] = data[s_harcama].apply(temiz_sayi_yap)
            data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
            
            display_data = pd.DataFrame()
            display_data[s_etiket] = data[s_etiket].fillna("").astype(str)
            display_data[s_basi] = data['Basi_Num'].apply(tr_format)
            display_data[s_revize] = data['Revize_Num'].apply(tr_format)
            display_data[s_harcama] = data['Harcama_Num'].apply(tr_format)
            display_data[s_kalan] = data['Kalan_Num'].apply(tr_format)
            
            for col in columns:
                if col not in [s_etiket, s_basi, s_revize, s_harcama, s_kalan]:
                    display_data[col] = data[col].fillna("").astype(str)
            st.dataframe(display_data, use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
