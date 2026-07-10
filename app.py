import streamlit as st
import pandas as pd
import os
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode

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
        # Excel'i okuyoruz
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
        
        s_etiket = columns[0] # B Sütunu (İşin Türü / Sektör)
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
        
        # --- GERÇEK EXCEL PİVOT TABLO ALANI ---
        st.subheader("🔍 Orijinal Pivot ve Alt İş Takip Tablosu")
        
        # Ag-Grid için veri setini hazırlıyoruz
        # Ana başlıkları (Sektörleri) belirlemek için bir mantık kuruyoruz
        ana_isler = []
        for x in data[s_etiket].fillna("").astype(str):
            x_temiz = x.strip()
            if x_temiz.isupper() and not any(t in x_temiz for t in ["TOPLAM", "Toplam", "GENEL"]):
                if x_temiz not in ana_isler:
                    ana_isler.append(x_temiz)
        
        # Tabloya ait satırların hangi ana başlığa ait olduğunu eşleştiriyoruz (Hiyerarşi Grubu)
        grup_kolon = []
        guncel_grup = "DİĞER"
        
        for val in data[s_etiket].fillna("").astype(str):
            val_temiz = val.strip()
            if val_temiz in ana_isler:
                guncel_grup = val_temiz
            grup_kolon.append(guncel_grup)
            
        grid_data = pd.DataFrame()
        grid_data['Ana İş Kalemi (Sektör)'] = grup_kolon
        grid_data['İŞİN ADI / DETAYI'] = data[s_etiket].fillna("").astype(str)
        grid_data[s_basi] = data['Basi_Num'].apply(tr_format)
        grid_data[s_revize] = data['Revize_Num'].apply(tr_format)
        grid_data[s_harcama] = data['Harcama_Num'].apply(tr_format)
        grid_data[s_kalan] = data['Kalan_Num'].apply(tr_format)
        
        # Diğer ek sütunları ekle
        for col in columns:
            if col not in [s_etiket, s_basi, s_revize, s_harcama, s_kalan]:
                grid_data[col] = data[col].fillna("").astype(str)
                
        # Toplam satırlarını grid içinden gizle (Karmaşayı önlemek için)
        grid_data = grid_data[~grid_data['İŞİN ADI / DETAYI'].str.contains('Toplam|TOPLAM', case=False)]
        
        # AG-GRID YAPILANDIRMASI (Excel Ağaç Görünümü Aktif Ediliyor)
        gb = GridOptionsBuilder.from_dataframe(grid_data)
        gb.configure_column('Ana İş Kalemi (Sektör)', rowGroup=True, hide=True) # Sektöre göre grupla ve o sütunu gizle
        gb.configure_column('İŞİN ADI / DETAYI', width=300)
        gb.configure_grid_options(animateRows=True, groupDisplayType='groupRows') # Satır içi açılır kapanır pivot yapısı
        
        gridOptions = gb.build()
        
        # Tabloyu Ekrana Basıyoruz
        AgGrid(
            grid_data,
            gridOptions=gridOptions,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            fit_columns_on_grid_load=True,
            theme='balham', # Kurumsal, temiz ve düz tablo teması
            enable_enterprise_modules=True
        )
        
    except Exception as e:
        st.error(f"Veri işlenirken bir hata oluştu: {e}")
else:
    st.error("Harcama.xlsx dosyası sistemde bulunamadı.")
