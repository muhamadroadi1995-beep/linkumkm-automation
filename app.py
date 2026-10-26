import streamlit as st
import asyncio
import sys
import io

st.set_page_config(page_title="Portal Jasa Entry Data LinkUMKM BRI", layout="centered")

st.title("⚡ Portal Automation LinkUMKM BRI")
st.markdown("---")

# Pilihan Menu Mode
mode = st.selectbox(
    "Pilih Mode Operasi Automation:",
    ("New Scoring (Pendaftaran & Skoring Baru)", "Rescoring (Skoring Ulang)")
)

url_target = st.text_input("URL Target Mantri BRI:", value="https://linkumkm.bri.co.id/umkmscore/mantri/175964")
jumlah_user = st.number_input("Jumlah Pengguna yang Ingin Diproses:", min_value=1, max_value=100, value=10)

if st.button("🚀 Jalankan Automation Sekarang", type="primary"):
    st.info(f"Memproses {jumlah_user} data dengan mode **{mode}**... Mohon tunggu, proses berjalan di latar belakang.")
    
    # Placeholder untuk log output terminal di web
    log_output = st.empty()
    log_output.text("Menyiapkan browser dan OCR AI...")
    
    # Jalankan script sesuai pilihan
    try:
        if "New Scoring" in mode:
            import NEWSCORINGPERFECT as target_script
        else:
            import RESCORINGPERFEC as target_script
            
        # Update URL target jika diubah di web
        target_script.URL_TARGET = url_target
        target_script.JUMLAH_PENGGUNA = int(jumlah_user)
        
        # Eksekusi fungsi async main dari script
        asyncio.run(target_script.main())
        st.success("✅ Proses Automation Selesai Tuntas!")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat eksekusi: {e}")
