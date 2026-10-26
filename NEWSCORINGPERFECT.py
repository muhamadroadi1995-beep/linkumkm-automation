import asyncio
import re
import random
import io
import ddddocr
from PIL import Image
from faker import Faker
from playwright.async_api import async_playwright

# --- KONFIGURASI UTAMA ---
JUMLAH_PENGGUNA = 50   # Jumlah total pengguna yang diinginkan
URL_TARGET = "https://linkumkm.bri.co.id/umkmscore/mantri/175964"
MAX_CONCURRENT = 4       # Membatasi maksimal 5 browser berjalan bersamaan

fake = Faker('id_ID')
DAFTAR_SEKTOR_USAHA = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

# Inisialisasi OCR Engine & Semaphore pembatas antrean
ocr_engine = ddddocr.DdddOcr(show_ad=False)
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def safe_click(page, locator, delay=1.2):
    """Fungsi klik aman dengan jeda manusia."""
    try:
        await locator.scroll_into_view_if_needed()
        await locator.wait_for(state="visible", timeout=10000)
        await locator.click(timeout=5000)
    except Exception:
        await locator.evaluate("elem => elem.click()")
    
    if delay > 0:
        await asyncio.sleep(delay)

def generate_single_user(user_id):
    """Membuat 1 data pengguna baru secara dinamis."""
    nik_acak = '32' + str(random.randint(10, 99)) + ''.join([str(random.randint(0, 9)) for _ in range(12)])
    telepon_acak = '08' + str(random.randint(11, 99)) + ''.join([str(random.randint(0, 9)) for _ in range(8)])
    tanggal_lahir_acak = fake.date_of_birth(minimum_age=25, maximum_age=60).strftime('%Y-%m-%d')
    sektor_usaha_acak = random.choice(DAFTAR_SEKTOR_USAHA)
    
    username_clean = re.sub(r'[^a-zA-Z0-9]', '', fake.first_name().lower())
    email_gmail = f"{username_clean}{random.randint(100000, 999999)}@gmail.com"

    return {
        "id": user_id,
        "nama": fake.name(),
        "email": email_gmail,
        "telepon": telepon_acak,
        "nik": nik_acak,
        "password": "Abcd123*",
        "tanggal_lahir": tanggal_lahir_acak,
        "sektor_usaha": sektor_usaha_acak,
        "url": URL_TARGET
    }

def generate_users_data(jumlah, start_id=1):
    """Membuat sekumpulan data pengguna baru."""
    return [generate_single_user(start_id + i) for i in range(jumlah)]

async def solve_captcha_ai(page):
    """Membaca CAPTCHA menggunakan AI ddddocr."""
    try:
        captcha_selectors = [
            "img[src*='captcha' i]", 
            "img[src*='Captcha' i]", 
            "img[src*='data:image']", 
            ".captcha img", 
            "#captcha_img", 
            "form img"
        ]
        
        captcha_img = None
        for selector in captcha_selectors:
            loc = page.locator(selector).first
            if await loc.count() > 0 and await loc.is_visible():
                captcha_img = loc
                break

        if not captcha_img:
            captcha_img = page.locator("form img").first
            await captcha_img.wait_for(state="visible", timeout=10000)

        img_bytes = await captcha_img.screenshot()
        result = ocr_engine.classification(img_bytes)
        
        clean_text = re.sub(r'[^A-Z0-9]', '', result.upper())
        return clean_text[:5].strip()

    except Exception as e:
        print(f"  [!] Gagal mengambil/membaca CAPTCHA: {e}")
        return ""

async def isi_captcha_ke_form(page, captcha_text):
    """Mengisikan CAPTCHA dengan simulasi ketikan manusia lambat."""
    input_selectors = [
        "input[name*='captcha' i]",
        "input[id*='captcha' i]",
        "input[placeholder*='captcha' i]",
        "input[name='sec_code']",
        "input[name='code']",
        ".captcha-input input"
    ]

    captcha_input = None
    for selector in input_selectors:
        loc = page.locator(selector).first
        if await loc.count() > 0 and await loc.is_visible():
            captcha_input = loc
            break

    if captcha_input:
        await captcha_input.click()
        await captcha_input.fill("")
        await asyncio.sleep(0.5)
        
        await captcha_input.press_sequentially(captcha_text, delay=200)
        await asyncio.sleep(0.5)
        
        await captcha_input.dispatch_event("input")
        await captcha_input.dispatch_event("change")
        await captcha_input.dispatch_event("blur")
        return True
    else:
        print("  [!] Kotak input CAPTCHA tidak ditemukan!")
        return False

async def proses_lanjutan_otomatis(context, page, user_data):
    """Fase 2: Menjalankan data diri lanjutan & skoring otomatis."""
    try:
        print(f"\n[⚡ PROSES] FASE 2 DIMULAI UNTUK USER ID #{user_data['id']}: {user_data['nama']}")

        # --- 1. Pengisian Data Diri Lanjutan ---
        print(f"  [User #{user_data['id']}] 1/4 Mengisi Data Diri Lanjutan...")
        tgl_input = page.get_by_placeholder("Masukkan Tanggal Lahir")
        await tgl_input.wait_for(state="visible", timeout=15000)
        await tgl_input.fill(user_data['tanggal_lahir'])

        sector_select = page.locator("select[name=\"business_sector\"]")
        await sector_select.wait_for(state="visible")
        await sector_select.select_option(user_data['sektor_usaha'])
        
        await page.locator("textarea[name=\"produced\"]").fill("ADA")
        await page.locator("textarea[name=\"business_address\"]").fill("ADA")
                                    
        # Dropdown Wilayah Berantai
        dropdowns = [
            ("select[name=\"province\"]", "32"),
            ("select[name=\"regency\"]", "3209"),
            ("select[name=\"subdistrict\"]", "3209200"),
            ("select[name=\"village\"]", "3209200017"),
            ("select[name=\"postal_code\"]", "30325")
        ]
        
        for selector, val in dropdowns:
            elem = page.locator(selector)
            await elem.wait_for(state="visible", timeout=10000)
            await elem.select_option(val)
            await asyncio.sleep(0.5)

        await page.get_by_role("radio", name="Tidak").check()
        await page.locator("#syarat").check()
        
        await safe_click(page, page.get_by_role("button", name="Lanjut"), delay=1)
        await safe_click(page, page.get_by_role("button", name="Saya Setuju"), delay=1)

        # --- 2. Halaman Skoring Pertama ---
        print(f"  [User #{user_data['id']}] 2/4 Membuka Form Skoring Pertama...")
        await safe_click(page, page.get_by_role("link", name="Mulai Skoring"), delay=2)
        await page.wait_for_load_state("domcontentloaded")

        # --- 3. Survey Skoring Pertama ---
        print(f"  [User #{user_data['id']}] 3/4 Pengisian Survey Skoring Pertama...")
        
        await page.locator("label").filter(has_text="Kurang dari Rp100 juta/tahun").wait_for(state="visible", timeout=15000)
        await page.locator("label").filter(has_text="Kurang dari Rp100 juta/tahun").click()
        await safe_click(page, page.get_by_text("Di bawah atau sama dengan"))
        await safe_click(page, page.get_by_text("1 Orang"))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Tidak", exact=True).first)
        await safe_click(page, page.get_by_text("Tidak", exact=True).nth(1))
        await safe_click(page, page.get_by_text("Tidak", exact=True).nth(2))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Tidak", exact=True).first)
        await safe_click(page, page.get_by_text("Ya, Sebagian").nth(1))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Tidak, masih di satu provinsi"))
        await safe_click(page, page.get_by_text("Menggunakan media sosial ("))
        await safe_click(page, page.get_by_text("Ya, Sebagian").first)
        await safe_click(page, page.get_by_text("Ya, Sebagian").nth(1))
        await safe_click(page, page.get_by_text("Ya, Sebagian").nth(2))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Membuat prosedur tertulis"))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Ya", exact=True).first)
        await safe_click(page, page.get_by_text("Tidak", exact=True).nth(1))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Tidak", exact=True).first)
        await safe_click(page, page.get_by_text("Tidak, belum secara khusus"))
        await safe_click(page, page.get_by_text("Tidak", exact=True).nth(1))
        await safe_click(page, page.get_by_text("Tidak", exact=True).nth(2))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Belum memiliki dokumen"))
        await safe_click(page, page.get_by_text("NPWP atas nama badan usaha"))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Memastikan agar karyawan"))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Ya, tapi baru sebagian."))
        await safe_click(page, page.get_by_text("Tahu nama-nama atau merek"))
        await safe_click(page, page.get_by_role("link", name="Selanjutnya"), delay=0.8)

        await safe_click(page, page.get_by_text("Belum ada prosedur khusus"))
        await safe_click(page, page.get_by_text("Belum ada prosedur atau tim"))
        await safe_click(page, page.get_by_text("Saldo cadangan kas usaha saya"))
        await safe_click(page, page.get_by_text("Akses internet yang handal ("))

        await safe_click(page, page.get_by_role("link", name="Hitung Nilai Survey"), delay=1.5)
        await safe_click(page, page.get_by_role("link", name="Lihat Hasil Level UMKM Saya"), delay=2)

        print(f"  [✔] USER #{user_data['id']}: {user_data['nama']} SELESAI TUNTAS!")
        return True

    except Exception as e:
        print(f"  [✖] User #{user_data['id']} Gagal di Fase Lanjutan: {e}")
        return False

async def jalankan_per_pengguna(browser, user):
    """Mengeksekusi satu pengguna tunggal."""
    async with semaphore:
        print(f"\n[+] Membuka Browser untuk User ID #{user['id']}: {user['nama']}")
        
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        await page.bring_to_front()

        try:
            await page.goto(user['url'], wait_until="domcontentloaded")
            await asyncio.sleep(2.0)
            
            # --- PENGISIAN FORM UTAMA ---
            await page.get_by_role("textbox", name="Masukkan nama anda").press_sequentially(user['nama'], delay=60)
            await asyncio.sleep(0.6)
            
            await page.get_by_role("textbox", name="Masukkan nomor telepon anda").press_sequentially(user['telepon'], delay=60)
            await asyncio.sleep(0.6)
            
            await page.get_by_placeholder("Masukkan Email anda").press_sequentially(user['email'], delay=60)
            await asyncio.sleep(0.6)
            
            await page.get_by_placeholder("Masukkan NIK anda").press_sequentially(user['nik'], delay=60)
            await asyncio.sleep(0.6)
            
            pass_field = page.locator("form").filter(has_text="Nama Lengkap Nomor Telepon").locator("input[name=\"password\"]")
            await pass_field.press_sequentially(user['password'], delay=60)
            await asyncio.sleep(0.6)
            
            await page.locator("input[name=\"password_retype\"]").press_sequentially(user['password'], delay=60)
            await asyncio.sleep(1.2)
            
            # --- RETRY ENGINE CAPTCHA ---
            captcha_tercapai = False
            max_percobaan_captcha = 10
            
            for percobaan_cap in range(1, max_percobaan_captcha + 1):
                print(f"  [🤖OCR] User #{user['id']} Percobaan Captcha ke-{percobaan_cap}...")
                
                hasil_ai = await solve_captcha_ai(page)
                
                if len(hasil_ai) < 5:
                    print(f"  [!] Hasil AI '{hasil_ai}' Kurang dari 5 Karakter. Refresh gambar...")
                    try:
                        refresh_btn = page.locator("a[href*='refresh'], .btn-refresh-captcha, img[src*='captcha']").first
                        if await refresh_btn.is_visible():
                            await refresh_btn.click()
                            await asyncio.sleep(2.0)
                    except Exception:
                        pass
                    continue

                print(f"  [🤖 AI OCR] AI Tebak: '{hasil_ai}'")
                
                await isi_captcha_ke_form(page, hasil_ai)
                await asyncio.sleep(1.0)
                
                await safe_click(page, page.get_by_role("button", name="Daftar"), delay=2.5)
                
                tgl_elem = page.get_by_placeholder("Masukkan Tanggal Lahir")
                try:
                    await tgl_elem.wait_for(state="visible", timeout=5000)
                    print(f"  [✔] CAPTCHA Valid! Lolos ke Fase 2 untuk User #{user['id']}")
                    captcha_tercapai = True
                    break
                except Exception:
                    print("  [!] CAPTCHA Salah / Ditolak Server. Refresh & Mengulang...")
                    try:
                        refresh_btn = page.locator("a[href*='refresh'], .btn-refresh-captcha, img[src*='captcha']").first
                        if await refresh_btn.is_visible():
                            await refresh_btn.click()
                            await asyncio.sleep(2.0)
                    except Exception:
                        pass

            if captcha_tercapai:
                hasil_fase2 = await proses_lanjutan_otomatis(context, page, user)
                await context.close()
                return {"user": user, "status": hasil_fase2}
            else:
                print(f"  [✖] Gagal menyelesaikan CAPTCHA untuk User #{user['id']}.")
                await context.close()
                return {"user": user, "status": False}

        except Exception as e:
            print(f"  [✖] Gagal pada User #{user['id']}: {e}")
            try:
                await context.close()
            except:
                pass
            return {"user": user, "status": False}

async def main():
    total_berhasil_sekarang = 0
    putaran = 1
    next_user_id = 1

    # Putaran pertama: langsung generate sejumlah JUMLAH_PENGGUNA (60)
    jumlah_yang_harus_dibuat = JUMLAH_PENGGUNA

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--start-maximized"])

        while total_berhasil_sekarang < JUMLAH_PENGGUNA:
            print("\n" + "=" * 65)
            print(f" PUTARAN KE-{putaran} | BERHASIL TERKUMPUL: {total_berhasil_sekarang}/{JUMLAH_PENGGUNA}")
            print(f" MEMPROSES {jumlah_yang_harus_dibuat} PENGGUNA BARU...")
            print("=" * 65)

            # Generate data pengguna baru sesuai jumlah yang gagal/kurang
            pengguna_baru = generate_users_data(jumlah_yang_harus_dibuat, start_id=next_user_id)
            next_user_id += jumlah_yang_harus_dibuat

            # Jalankan tugas secara paralel
            tasks = [jalankan_per_pengguna(browser, user) for user in pengguna_baru]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            berhasil_di_putaran_ini = 0
            gagal_di_putaran_ini = 0

            for r in results:
                if isinstance(r, dict) and r["status"] is True:
                    berhasil_di_putaran_ini += 1
                else:
                    gagal_di_putaran_ini += 1

            total_berhasil_sekarang += berhasil_di_putaran_ini

            print(f"\n[📊 REKAP PUTARAN {putaran}] Berhasil: {berhasil_di_putaran_ini} | Gagal: {gagal_di_putaran_ini}")
            print(f"Total Berhasil Kumulatif: {total_berhasil_sekarang}/{JUMLAH_PENGGUNA}")

            # Jika masih ada yang gagal, atur jumlah pembuatan berikutnya persis sejumlah yang gagal saja
            if total_berhasil_sekarang < JUMLAH_PENGGUNA:
                jumlah_yang_harus_dibuat = gagal_di_putaran_ini
                print(f"[🔄 OTOMATIS] Masih ada {gagal_di_putaran_ini} yang gagal. Membuat {gagal_di_putaran_ini} data baru untuk digantikan...")
                await asyncio.sleep(3.0)

            putaran += 1

        await browser.close()

    print("\n" + "=" * 50)
    print("RINGKASAN AKHIR EKSEKUSI")
    print(f"Target Sukses Tercapai : {total_berhasil_sekarang} / {JUMLAH_PENGGUNA}")
    print("STATUS                 : SEMUA BERHASIL TUNTAS (GAGAL = 0)")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
