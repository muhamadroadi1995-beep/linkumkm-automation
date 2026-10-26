import streamlit as st
import asyncio
import os
import sys

# AUTO-INSTALL PLAYWRIGHT BROWSER DI CLOUD SERVER
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

st.set_page_config(page_title="Portal Jasa Entry Data LinkUMKM BRI", layout="centered")

st.title("⚡ Portal Automation LinkUMKM BRI")
st.markdown("---")

mode = st.selectbox(
    "Pilih Mode Operasi Automation:",
    ("New Scoring (Pendaftaran & Skoring Baru)", "Rescoring (Skoring Ulang)")
)

url_target = st.text_input("URL Target Mantri BRI:", value="https://linkumkm.bri.co.id/umkmscore/mantri/175964")
jumlah_user = st.number_input("Jumlah Pengguna yang Ingin Diproses:", min_value=1, max_value=100, value=5)

if st.button("🚀 Jalankan Automation Sekarang", type="primary"):
    st.info(f"Memproses {jumlah_user} data dengan mode **{mode}**... Mohon tunggu, proses berjalan di latar belakang.")
    
    try:
        if "New Scoring" in mode:
            import NEWSCORINGPERFECT as target_script
        else:
            import RESCORINGPERFEC as target_script
            
        target_script.URL_TARGET = url_target
        target_script.JUMLAH_PENGGUNA = int(jumlah_user)
        
        asyncio.run(target_script.main())
        st.success("✅ Proses Automation Selesai Tuntas!")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat eksekusi: {e}")
