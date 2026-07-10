import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Genişlik Ayarı
st.set_page_config(page_title="DSİ Yatırım İzleme Paneli", layout="wide")

st.title("📊 Yatırım İzleme ve Performans Raporlama Programı")
st.write("Excel dosyanızı yükleyerek güncel durumu anlık takip edebilirsiniz.")

# Dosya Yükleme Alanı
uploaded_file = st.file_uploader("Lütfen güncel Excel (Harcama.xlsx) dosyasını yükleyin", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Sayfa isimlerini kontrol et veya varsayılan olarak ilk sayfayı/veri sayfasını oku
        # Gerçek uygulamada 'Veri' sekmesini hedefliyoruz
        df = pd.read_excel(uploaded_file, sheet_name=None)
        
        # Sayfa seçimi (Kullanıcı isterse sekmeler arasında gezebilir)
        sayfalar = list(df.keys())
        secilen_sayfa = st.sidebar.selectbox("Görüntülenecek Sayfa/Veri Seti", sayfalar)
        
        data = df[secilen_sayfa]
        
        # Temel temizlik (Boş satırları uçur)
        data = data.dropna(how='all')
        
        st.success(f"'{secilen_sayfa}' sayfası başarıyla yüklendi! Toplam {len(data)} satır veri bulundu.")
        
        # --- ÖZET METRİKLER (Veri sekmesi için dinamik hesaplama) ---
        cols = data.columns
        # Sütun isimlerinde temizlik yapalım
        data.columns = [str(c).strip() for c in data.columns]
        
        if 'SENE BASI ODENEGI' in data.columns and 'REVIZE ODENEK' in data.columns:
            st.subheader("📌 Genel Ödenek ve Harcama Durumu")
            
            toplam_sene_basi = pd.to_numeric(data['SENE BASI ODENEGI'], errors='coerce').sum()
            toplam_revize = pd.to_numeric(data['REVIZE ODENEK'], errors='coerce').sum()
            toplam_harcama = pd.to_numeric(data['YILI HARCAMA'], errors='coerce').sum() if 'YILI HARCAMA' in data.columns else 0
            kalan_odenek = pd.to_numeric(data['YILI ÖDENEĞİ KALAN'], errors='coerce').sum() if 'YILI ÖDENEĞİ KALAN' in data.columns else (toplam_revize - toplam_harcama)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Toplam Sene Başı Ödeneği", f"{toplam_sene_basi:,.2f} TL")
            m2.metric("Toplam Revize Ödenek", f"{toplam_revize:,.2f} TL")
            m3.metric("Toplam Yılı Harcaması", f"{toplam_harcama:,.2f} TL")
            m4.metric("Kalan Ödenek Bakiyesi", f"{kalan_odenek:,.2f} TL")
            
            # --- GRAFİK ALANI ---
            st.subheader("📈 İş Türlerine Göre Ödenek Dağılımı")
            if 'İŞİN TÜRÜ' in data.columns:
                grafik_data = data.groupby('İŞİN TÜRÜ')['REVIZE ODENEK'].sum().reset_index()
                fig = px.bar(grafik_data, x='İŞİN TÜRÜ', y='REVIZE ODENEK', title="İş Türü bazında Revize Ödenekler", color='İŞİN TÜRÜ')
                st.plotly_chart(fig, use_container_width=True)
        
        # --- AKILLI ARAMA MOTORU ---
        st.subheader("🔍 Akıllı İş/Proje Sorgulama Odası")
        arama_terimi = st.text_input("Aramak istediğiniz işin adını, yerini veya türünü yazın (Örn: Afyonkarahisar, Gölet, Sayaç):")
        
        if arama_terimi:
            # Tüm sütunlarda arama yapabilmek için metne çevirip filtreliyoruz
            mask = data.astype(str).apply(lambda x: x.str.contains(arama_terimi, case=False)).any(axis=1)
            filtreli_data = data[mask]
            st.write(f"🔍 '{arama_terimi}' araması için {len(filtreli_data)} sonuç bulundu:")
            st.dataframe(filtreli_data)
        else:
            st.write("Tüm Veri Listesi (İlk 100 Satır):")
            st.dataframe(data.head(100))
            
    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu. Lütfen Excel formatını kontrol edin. Hata: {e}")
else:
    st.info("💡 Başlamak için lütfen bilgisayarınızdaki güncel 'Harcama.xlsx' dosyasını yukarıdaki alana yükleyin.")
