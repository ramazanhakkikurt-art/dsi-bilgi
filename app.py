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
        raw_data = df[secilen_sayfa].dropna(how='all')
        
        header_row_idx = 0
        for idx, row in raw_data.iterrows():
            if row.astype(str).str.contains('Satır Etiketleri|İŞİN TÜRÜ|İŞİN ADI|PROJE NO').any():
                header_row_idx = idx
                break
                
        columns = raw_data.loc[header_row_idx].astype(str).str.strip().tolist()
        data = raw_data.loc[header_row_idx + 1:].copy()
        data.columns = columns
        
        st.success(f"📌 '{secilen_sayfa}' Verileri Canlı Olarak Gösteriliyor.")
        
        # Sütun tespiti ve sayısal dönüşümler
        s_tur = columns[1] if 'TÜRÜ' in columns[1] or 'TURU' in columns[1] else [c for c in columns if 'TÜRÜ' in c or 'TURU' in c][0]
        s_adi = [c for c in columns if 'ADI' in c or 'İŞ' in c or 'is_adi' in c][0]
        s_basi = [c for c in columns if 'SENE' in c or 'BAŞI' in c or 'BASI' in c][0]
        s_revize = [c for c in columns if 'REVİZE' in c or 'REVIZE' in c][0]
        s_harcama = [c for c in columns if 'HARCAMA' in c or 'YILI' in c][0]
        s_kalan = [c for c in columns if 'KALAN' in c or 'ÖDENEĞİ KALAN' in c][0]
        
        # Performans sütununu bul
        s_perf = [c for c in columns if 'PERFORMANS' in c or 'PERF' in c][0]
        
        data['Basi_Num'] = data[s_basi].apply(temiz_sayi_yap)
        data['Revize_Num'] = data[s_revize].apply(temiz_sayi_yap)
        data['Harcama_Num'] = data[s_harcama].apply(temiz_sayi_yap)
        data['Kalan_Num'] = data['Revize_Num'] - data['Harcama_Num']
        
        # Toplam ve harici satırları temizle, saf veriyi al
        saf_veri = data[
            (~data[s_tur].astype(str).str.contains('Toplam|TOPLAM|Genel', case=False, na=False)) & 
            (data[s_tur].fillna("").astype(str).str.strip() != "")
        ].copy()
        
        # --- ÖZET METRİKLER ---
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
        grafik_ozet = saf_veri.groupby(s_tur)['Revize_Num'].sum().reset_index()
        if not grafik_ozet.empty:
            fig = px.pie(grafik_ozet, names=s_tur, values='Revize_Num', hole=0.4)
            fig.update_traces(textinfo='none', hovertemplate="<b>%{label}</b><br>Ödenek: %{value:,.2f} TL<br>Pay: %{percent}<extra></extra>")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig, use_container_width=True)
            
        # Gösterim veri çerçevesini hazırla
        display_df = pd.DataFrame()
        display_df["İŞİN TÜRÜ"] = saf_veri[s_tur].astype(str)
        display_df["İŞİN ADI"] = saf_veri[s_adi].astype(str)
        display_df["SENE BAŞI ÖDENEĞİ"] = saf_veri['Basi_Num']
        display_df["REVİZE ÖDENEK"] = saf_veri['Revize_Num']
        display_df["YILI HARCAMASI"] = saf_veri['Harcama_Num']
        display_df["YILI ÖDENEĞİ KALAN"] = saf_veri['Kalan_Num']
        display_df["PERFORMANS"] = saf_veri[s_perf].fillna("0").astype(str).str.strip()
        
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
        
        # --- TABLO 2: SADECE PERFORMANS İŞLERİ ---
        st.subheader("🎯 Sadece Performans Takibindeki İşler")
        # Performans kolonu 1 veya 1.0 olan satırları jilet gibi filtreliyoruz
        perf_mask = display_df["PERFORMANS"].isin(["1", "1.0", 1, 1.0])
        perf_df = display_df[perf_mask].copy()
        
        if not perf_df.empty:
            st.dataframe(
                perf_df[["İŞİN TÜRÜ", "İŞİN ADI", "SENE BAŞI ÖDENEĞİ", "REVİZE ÖDENEK", "YILI HARCAMASI", "YILI ÖDENEĞİ KALAN"]],
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
            st.warning("Bu sayfada performans işi olarak işaretlenmiş bir kayıt bulunamadı.")
            
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
