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
        
        # Excel'i sütun indekslerine göre kararlı okumak için başlığı uçurmadan ham alıyoruz
        raw_data = df[secilen_sayfa].dropna(how='all')
        
        # Başlık satırını bul
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ|İŞİN ADI|PROJE NO').any():
                header_row_idx = idx
                break
        
        # Veriyi ve sütunları ayır
        data = raw_data.loc[header_row_idx + 1:].copy()
        
        # Sütunları indeks numaralarına göre kesin olarak eşliyoruz (İsimlerden bağımsız)
        # B Sütunu (1. İndeks) -> İŞİN TÜRÜ
        # C Sütunu (2. İndeks) -> İŞİN ADI
        # D Sütunu (3. İndeks) -> SENE BAŞI ÖDENEĞİ
        # E Sütunu (4. İndeks) -> REVİZE ÖDENEK
        # F Sütunu (5. İndeks) -> YILI HARCAMASI
        # K Sütunu (10. İndeks) -> Performans İşaret Sütunu (1 olanlar)
        
        # Sütun sayılarını kontrol et (Hata vermemesi için koruma)
        if raw_data.shape[1] >= 6:
            data['Tur_Val'] = data.iloc[:, 1].fillna("").astype(str).str.strip()
            data['Adi_Val'] = data.iloc[:, 2].fillna("").astype(str).str.strip()
            data['Basi_Num'] = data.iloc[:, 3].apply(temiz_sayi_yap)
            data['Revize_Num'] = data.iloc[:, 4].apply(temiz_sayi_yap)
            data['Harcama_Num'] = data.iloc[:, 5].apply(temiz_sayi_yap)
            data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
            
            # K sütunu var mı kontrol et (Eğer en az 11 sütun varsa 10. indekstedir)
            if raw_data.shape[1] >= 11:
                data['K_Sutunu'] = data.iloc[:, 10].fillna("0").astype(str).str.strip().str.replace(".0", "", regex=False)
            else:
                data['K_Sutunu'] = "0"
                
            st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
            
            # Toplam satırlarını listeden ayıkla
            saf_veri = data[
                (~data['Tur_Val'].str.contains('Toplam|TOPLAM|Genel', case=False, na=False)) & 
                (data['Tur_Val'] != "")
            ].copy()
            
            # --- ÜST ÖZET METRİKLER ---
            st.subheader("💰 Genel Ödenek ve Harcama Özeti")
            t_basi = saf_veri['Basi_Num'].sum()
            t_revize = saf_veri['Revize_Num'].sum()
            t_harcama = saf_veri['Harcama_Num'].sum()
            t_kalan = t_revize - t_harcama
            
            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Sene Başı Ödeneği</h4><h3 style='color:#38bdf8; font-size:20px;'>{tr_format(t_basi)} TL</h3></div>", unsafe_allow_html=True)
            m2.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Revize Ödenek</h4><h3 style='color:#fbbf24; font-size:20px;'>{tr_format(t_revize)} TL</h3></div>", unsafe_allow_html=True)
            m3.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Yılı Harcaması</h4><h3 style='color:#34d399; font-size:20px;'>{tr_format(t_harcama)} TL</h3></div>", unsafe_allow_html=True)
            m4.markdown(f"<div style='background-color:#1e293b; padding:15px; border-radius:10px;'><h4>Kalan Ödenek</h4><h3 style='color:#f87171; font-size:20px;'>{tr_format(t_kalan)} TL</h3></div>", unsafe_allow_html=True)
            
            # --- PASTA GRAFİĞİ ---
            st.subheader("🍕 Sektörlere Göre Bütçe Dağılımı")
            grafik_ozet = saf_veri.groupby('Tur_Val')['Revize_Num'].sum().reset_index()
            if not grafik_ozet.empty:
                fig = px.pie(grafik_ozet, names='Tur_Val', values='Revize_Num', hole=0.4)
                fig.update_traces(textinfo='none', hovertemplate="<b>%{label}</b><br>Ödenek: %{value:,.2f} TL<br>Pay: %{percent}<extra></extra>")
                fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig, use_container_width=True)
            
            # Gösterim DataFrame'i
            display_df = pd.DataFrame()
            display_df["İŞİN TÜRÜ"] = saf_veri['Tur_Val']
            display_df["İŞİN ADI"] = saf_veri['Adi_Val']
            display_df["SENE BAŞI ÖDENEĞİ"] = saf_veri['Basi_Num']
            display_df["REVİZE ÖDENEK"] = saf_veri['Revize_Num']
            display_df["YILI HARCAMASI"] = saf_veri['Harcama_Num']
            display_df["YILI ÖDENEĞİ KALAN"] = saf_veri['Kalan_Num']
            display_df["K_FILTRE"] = saf_veri['K_Sutunu']
            
            # --- TABLO 1: GENEL PROJE LİSTESİ ---
            st.subheader("📋 Genel İş ve Proje Listesi (Tümü)")
            st.dataframe(
                display_df[["İŞİN TÜRÜ", "İŞİN ADI", "SENE BAŞI ÖDENEĞİ", "REVİZE ÖDENEK", "YILI HARCAMASI", "YILI ÖDENEĞİ KALAN"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "SENE BAŞI ÖDENEĞİ": st.column_config.NumberColumn(format="%.2f TL"),
                    "REVİZE ÖDENEK": st.column_config.NumberColumn(format="%.2f TL"),
                    "YILI HARCAMASI": st.column_config.NumberColumn(format="%.2f TL"),
                    "YILI ÖDENEĞİ KALAN": st.column_config.NumberColumn(format="%.2f TL")
                }
            )
            
            # --- TABLO 2: K SÜTUNUNDA 1 YAZAN İŞLER ---
            st.subheader("🎯 K Sütununa Göre Seçilen Performans İşleri")
            
            # K Sütununda tam olarak 1 yazan kayıtları filtrele
            k_perf_df = display_df[display_df["K_FILTRE"] == "1"].copy()
            
            if not k_perf_df.empty:
                st.dataframe(
                    k_perf_df[["İŞİN TÜRÜ", "İŞİN ADI", "SENE BAŞI ÖDENEĞİ", "REVİZE ÖDENEK", "YILI HARCAMASI", "YILI ÖDENEĞİ KALAN"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "SENE BAŞI ÖDENEĞİ": st.column_config.NumberColumn(format="%.2f TL"),
                        "REVİZE ÖDENEK": st.column_config.NumberColumn(format="%.2f TL"),
                        "YILI HARCAMASI": st.column_config.NumberColumn(format="%.2f TL"),
                        "YILI ÖDENEĞİ KALAN": st.column_config.NumberColumn(format="%.2f TL")
                    }
                )
            else:
                st.info("Bu sayfada K sütununda '1' olarak işaretlenmiş bir kayıt bulunamadı.")
        else:
            st.error("Excel dosyasında yeterli sütun bulunamadı.")
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
