import streamlit as st
import asyncio
import os

# AUTO-INSTALL PLAYWRIGHT BROWSER DI CLOUD SERVER
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()

# --- KONFIGURASI TAMPILAN DASHBOARD MEWAH (KORPORAT STYLE) ---
st.set_page_config(
    page_title="Executive Portal | LinkUMKM BRI", 
    page_icon="🛡️", 
    layout="wide"
)

# Custom Styling CSS
st.markdown("""
    <style>
    .main-banner {
        background: linear-gradient(135deg, #0A192F 0%, #172A45 100%);
        padding: 35px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .operator-card {
        background: rgba(255, 255, 255, 0.08);
        padding: 12px 20px;
        border-radius: 12px;
        border-left: 4px solid #64FFDA;
        margin-top: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .section-box {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .login-container {
        max-width: 420px;
        margin: 60px auto;
        padding: 35px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Session State untuk Status Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOGIN OPERATOR ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("""
            <div class="login-container">
                <h2 style="text-align: center; color: #0A192F; margin-bottom: 5px;">🔐 Portal Login</h2>
                <p style="text-align: center; color: #646b74; font-size: 13px; margin-bottom: 25px;">Otorisasi Khusus Operator LinkUMKM BRI</p>
        """, unsafe_allow_html=True)
        
        user_input = st.text_input("Nama Pengguna (Username)")
        pass_input = st.text_input("Kata Sandi (Password)", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔑 Masuk ke Dashboard", type="primary", use_container_width=True):
            # Kredensial Akses Operator
            if user_input == "Muhamad Roadi" and pass_input == "13Mei2022":
                st.session_state.logged_in = True
                st.success("Login Berhasil! Mengalihkan...")
                st.rerun()
            else:
                st.error("❌ Nama pengguna atau kata sandi salah!")
                
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- DASHBOARD UTAMA (SETELAH BERHASIL LOGIN) ---
    
    # Tombol Logout di Sidebar atas
    with st.sidebar:
        st.markdown("### 👤 Sesi Aktif")
        st.write("**Operator:** Muhamad Roadi")
        st.write("**Unit:** Bank BRI AWN 2")
        if st.button("🚪 Keluar (Logout)", type="secondary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
        st.markdown("### ⚙️ Pengaturan Sistem")
        
        mode_operasi = st.selectbox(
            "Pilih Mode Operasi:",
            ("New Scoring (Pendaftaran Baru)", "Rescoring (Skoring Ulang)")
        )
        
        url_target = st.text_input(
            "URL Target Mantri BRI:", 
            value="https://linkumkm.bri.co.id/umkmscore/mantri/175964"
        )

    # HEADER DASHBOARD EKSKLUSIF
    st.markdown("""
        <div class="main-banner">
            <h1 style="margin:0; font-size: 30px; font-weight: 700;">🛡️ Executive LinkUMKM Automation Portal</h1>
            <p style="margin:8px 0 0 0; opacity: 0.8; font-size: 15px;">Sistem Otomatisasi Skoring & Pendaftaran Mandiri Berbasis AI</p>
            <div class="operator-card">
                <div>
                    <span style="font-size: 13px; opacity: 0.7; display: block;">VERIFIED OPERATOR</span>
                    <b style="font-size: 16px; color: #64FFDA;">Muhamad Roadi</b>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 13px; opacity: 0.7; display: block;">STATUS KEAMANAN</span>
                    <b style="font-size: 15px; color: #64FFDA;">🟢 Sesi Terotorisasi Aman</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # KONTROL UTAMA (MANAJEMEN KONSUMEN & APPROVAL)
    col_konsumen, col_approval = st.columns([1.3, 0.7], gap="large")

    with col_konsumen:
        st.markdown("""
            <div class="section-box">
                <h3>👥 Manajemen Data Konsumen</h3>
                <p style="font-size: 14px; color: #646b74;">Tuliskan atau sesuaikan daftar nama konsumen yang akan diproses melalui sistem otomatisasi.</p>
            </div>
        """, unsafe_allow_html=True)
        
        input_nama_konsumen = st.text_area(
            "Daftar Nama Konsumen (1 Nama per Baris):",
            value="H. Ahmad Suyudi\nSiti Aminah\nBudi Santoso",
            height=160,
            help="Ubah atau tambah nama konsumen sesuai kebutuhan."
        )
        
        daftar_konsumen = [item.strip() for item in input_nama_konsumen.split("\n") if item.strip()]
        st.metric(label="Total Antrean Konsumen Siap Eksekusi", value=f"{len(daftar_konsumen)} Orang")

    with col_approval:
        st.markdown("""
            <div class="section-box" style="border-left: 5px solid #003366;">
                <h3>🔐 Panel Otorisasi Operator</h3>
                <p style="font-size: 14px; color: #646b74;">Konfirmasi akhir oleh operator yang berwenang.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
            * **Operator Valid:** Muhamad Roadi
            * **Jumlah Data Masuk:** `{len(daftar_konsumen)} Data`
            * **Mode Terpilih:** `{mode_operasi}`
        """)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        persetujuan_mutlak = st.checkbox(
            "✅ **Saya, Muhamad Roadi, menyatakan data konsumen di samping sudah valid dan memberikan izin untuk mengeksekusi sistem.**",
            value=False
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        tombol_eksekusi = st.button(
            "🚀 Eksekusi Sistem Sekarang", 
            type="primary", 
            use_container_width=True,
            disabled=not persetujuan_mutlak
        )

    # AREA EKSEKUSI & LOG LIVE
    if tombol_eksekusi:
        if not persetujuan_mutlak:
            st.error("⚠️ Akses ditolak. Operator wajib mencentang kotak persetujuan sebelum menjalankan sistem.")
        else:
            st.markdown("---")
            st.markdown("### 📊 Status Live Eksekusi Automation")
            
            with st.status("⚡ Menyiapkan Mesin Browser & AI OCR...", expanded=True) as status_box:
                st.write(f"👤 **Otorisasi Diterima dari:** Muhamad Roadi")
                st.write(f"🎯 **Endpoint Target:** `{url_target}`")
                st.write(f"📦 **Jumlah Target Diproses:** {len(daftar_konsumen)} konsumen.")
                
                try:
                    if "New Scoring" in mode_operasi:
                        import NEWSCORINGPERFECT as target_script
                    else:
                        import RESCORINGPERFEC as target_script
                        
                    target_script.URL_TARGET = url_target
                    target_script.JUMLAH_PENGGUNA = len(daftar_konsumen)
                    
                    st.write("🤖 Menjalankan skrip Playwright paralel dan ddddocr...")
                    asyncio.run(target_script.main())
                    
                    status_box.update(label="✅ Seluruh Proses Berhasil Selesai Tuntas!", state="complete", expanded=False)
                    st.success("🎉 Berhasil! Data seluruh konsumen telah diproses secara otomatis oleh sistem.")
                    
                except Exception as err:
                    status_box.update(label="❌ Terjadi Gangguan Saat Eksekusi", state="error", expanded=True)
                    st.error(f"Pesan Error: {err}")
