import streamlit as st
import asyncio
import os
import random
from faker import Faker

# AUTO-INSTALL PLAYWRIGHT BROWSER DI CLOUD SERVER
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium")

install_playwright()
fake = Faker('id_ID')

# --- KONFIGURASI TAMPILAN DASHBOARD MEWAH ---
st.set_page_config(
    page_title="Portal LinkUMKM BRI | Layanan & Operator", 
    page_icon="⚡", 
    layout="wide"
)

st.markdown("""
    <style>
    .main-banner {
        background: linear-gradient(135deg, #0A192F 0%, #172A45 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .card-box {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .login-box {
        max-width: 400px;
        margin: 40px auto;
        padding: 30px;
        background: #ffffff;
        border-radius: 14px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        border: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

# Inisialisasi Database Sesi Sementara (Session State) untuk Antrean Konsumen & Status Login
if "antrean_konsumen" not in st.session_state:
    st.session_state.antrean_konsumen = [
        {"id": 1, "nama": "H. Ahmad Suyudi", "telepon": "081234567890", "sektor": "1", "status": "Menunggu Persetujuan"},
        {"id": 2, "nama": "Siti Aminah", "telepon": "089876543210", "sektor": "3", "status": "Menunggu Persetujuan"}
    ]

if "operator_logged_in" not in st.session_state:
    st.session_state.operator_logged_in = False

# --- HEADER UTAMA ---
st.markdown("""
    <div class="main-banner">
        <h1 style="margin:0; font-size: 28px; font-weight: 700;">⚡ Portal Layanan & Otomatisasi LinkUMKM BRI</h1>
        <p style="margin:6px 0 0 0; opacity: 0.8; font-size: 14px;">Sistem Terintegrasi Konsumen & Verifikasi Eksekutif Operator</p>
    </div>
""", unsafe_allow_html=True)

# PILIH PORTAL (TAB NAVIGASI UTAMA)
tab_konsumen, tab_operator = st.tabs(["📝 Portal Pendaftaran Konsumen", "🔐 Portal Khusus Operator (Muhamad Roadi)"])

# ==========================================
# 1. PORTAL KHUSUS KONSUMEN
# ==========================================
with tab_konsumen:
    st.markdown("### 📋 Form Pengajuan Data Mandiri Konsumen")
    st.markdown("Silakan isi data usaha Anda di bawah ini. Data akan dikirimkan ke sistem antrean dan **wajib mendapatkan persetujuan dari Operator (Muhamad Roadi)** sebelum diproses ke sistem LinkUMKM BRI.")
    
    with st.form("form_pendaftaran_konsumen"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nama_konsumen = st.text_input("Nama Lengkap Sesuai KTP:")
            telepon_konsumen = st.text_input("Nomor WhatsApp/Telepon Aktif:")
        with col_f2:
            sektor_pilihan = st.selectbox(
                "Sektor Usaha:",
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                format_func=lambda x: f"Sektor Kategori {x}"
            )
            catatan_usaha = st.text_input("Nama / Jenis Usaha:", placeholder="Contoh: Warung Sembako / Konter")
            
        submit_konsumen = st.form_submit_button("📤 Kirim Data ke Antrean Operator", type="primary", use_container_width=True)
        
        if submit_konsumen:
            if nama_konsumen and telepon_konsumen:
                new_id = len(st.session_state.antrean_konsumen) + 1
                st.session_state.antrean_konsumen.append({
                    "id": new_id,
                    "nama": nama_konsumen,
                    "telepon": telepon_konsumen,
                    "sektor": sektor_pilihan,
                    "status": "Menunggu Persetujuan"
                })
                st.success(f"✅ Berhasil! Data atas nama **{nama_konsumen}** telah masuk ke antrean dan menunggu verifikasi Operator Muhamad Roadi.")
            else:
                st.warning("⚠️ Mohon lengkapi Nama Lengkap dan Nomor Telepon Anda.")

    st.markdown("---")
    st.info("ℹ️ **Informasi:** Konsumen hanya dapat mendaftarkan diri. Eksekusi otomatisasi sistem hanya dapat dijalankan setelah operator memberikan lampu hijau.")

# ==========================================
# 2. PORTAL KHUSUS OPERATOR
# ==========================================
with tab_operator:
    if not st.session_state.operator_logged_in:
        # TAMPILAN LOGIN OPERATOR
        st.markdown("<br>", unsafe_allow_html=True)
        col_l1, col_l2, col_l3 = st.columns([1, 1.2, 1])
        
        with col_l2:
            st.markdown("""
                <div class="login-box">
                    <h3 style="text-align: center; color: #0A192F; margin-bottom: 5px;">🔐 Login Operator</h3>
                    <p style="text-align: center; color: #646b74; font-size: 13px; margin-bottom: 20px;">Otorisasi Akses: Muhamad Roadi</p>
            """, unsafe_allow_html=True)
            
            username_op = st.text_input("Nama Pengguna:")
            password_op = st.text_input("Kata Sandi:", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Masuk Panel Operator", type="primary", use_container_width=True):
                if username_op == "Muhamad Roadi" and password_op == "13Mei2022":
                    st.session_state.operator_logged_in = True
                    st.success("Login Berhasil!")
                    st.rerun()
                else:
                    st.error("❌ Nama pengguna atau sandi salah!")
            st.markdown("</div>", unsafe_allow_html=True)
            
    else:
        # DASHBOARD UTAMA OPERATOR
        col_op_info, col_op_logout = st.columns([4, 1])
        with col_op_info:
            st.markdown("### 🛡️ Panel Kendali & Persetujuan Operator")
            st.write("Operator Aktif: **Muhamad Roadi** | Bank BRI AWN 2")
        with col_op_logout:
            if st.button("🚪 Keluar", use_container_width=True):
                st.session_state.operator_logged_in = False
                st.rerun()
                
        st.markdown("---")
        
        # Pengaturan Sistem di Panel Operator
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            mode_operasi = st.selectbox("Mode Operasi Automation:", ("New Scoring (Pendaftaran Baru)", "Rescoring (Skoring Ulang)"))
        with col_s2:
            url_target = st.text_input("URL Target Mantri BRI:", value="https://linkumkm.bri.co.id/umkmscore/mantri/175964")

        st.markdown("### 📥 Daftar Antrean Konsumen Masuk")
        st.markdown("Hanya data dengan status **Disetujui** yang akan diproses oleh mesin otomatisasi.")
        
        # Tabel Manajemen & Persetujuan Data
        if not st.session_state.antrean_konsumen:
            st.info("Belum ada data konsumen di antrean.")
        else:
            for idx, k in enumerate(st.session_state.antrean_konsumen):
                cols = st.columns([2, 1.5, 1, 1.5, 1])
                cols[0].write(f"**{k['nama']}**")
                cols[1].write(f"📞 {k['telepon']}")
                cols[2].write(f"Sektor: {k['sektor']}")
                
                # Status Badge
                if k['status'] == "Disetujui":
                    cols[3].success(k['status'])
                else:
                    cols[3].warning(k['status'])
                
                # Tombol Aksi Persetujuan oleh Operator
                if k['status'] == "Menunggu Persetujuan":
                    if cols[4].button("✅ Setujui", key=f"app_{idx}"):
                        st.session_state.antrean_konsumen[idx]['status'] = "Disetujui"
                        st.rerun()
                else:
                    if cols[4].button("❌ Batalkan", key=f"rev_{idx}"):
                        st.session_state.antrean_konsumen[idx]['status'] = "Menunggu Persetujuan"
                        st.rerun()

            st.markdown("---")
            
            # Filter data yang sudah disetujui operator
            data_disetujui = [item for item in st.session_state.antrean_konsumen if item['status'] == "Disetujui"]
            
            st.metric(label="Total Data Siap Dieksekusi (Telah Disetujui Operator)", value=f"{len(data_disetujui)} Orang")
            
            # Tombol Eksekusi Berdasarkan Data yang Disetujui Operator
            if st.button("🚀 Jalankan Automation untuk Data yang Disetujui", type="primary", disabled=len(data_disetujui) == 0):
                st.markdown("### 📊 Status Live Eksekusi Sistem")
                with st.status("⚡ Menjalankan Proses Otomatisasi Playwright...", expanded=True) as status_box:
                    st.write(f"🔐 **Otorisasi Mutlak:** Disetujui oleh Operator Muhamad Roadi")
                    st.write(f"🎯 **Target URL:** `{url_target}`")
                    st.write(f"👥 **Total Diproses:** {len(data_disetujui)} konsumen.")
                    
                    try:
                        if "New Scoring" in mode_operasi:
                            import NEWSCORINGPERFECT as target_script
                        else:
                            import RESCORINGPERFEC as target_script
                            
                        target_script.URL_TARGET = url_target
                        target_script.JUMLAH_PENGGUNA = len(data_disetujui)
                        
                        st.write("🤖 Menjalankan skrip background...")
                        asyncio.run(target_script.main())
                        
                        status_box.update(label="✅ Eksekusi Selesai Tuntas!", state="complete", expanded=False)
                        st.success("🎉 Seluruh data konsumen yang disetujui telah berhasil diproses!")
                    except Exception as err:
                        status_box.update(label="❌ Terjadi Kendala", state="error", expanded=True)
                        st.error(f"Error: {err}")
