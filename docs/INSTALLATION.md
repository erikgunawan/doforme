# Instalasi doforme

doforme adalah plugin Claude Code. Plugin dimuat dari checkout GitHub; instalasi
marketplace belum disediakan. Penggunaan lokal tidak memerlukan GitHub Actions,
Jira, Figma atau Telegram.

## Prasyarat

- Git dan Python 3.9 atau lebih baru. Helper memakai Python standard library.
- Claude Code dengan akun/model yang dapat digunakan. Versi CLI yang diuji: 2.1.323.
- Hak baca ke repo GitHub doforme dan repo target yang ingin diperiksa.
- Untuk workflow fix: Git checkout kecil yang terisolasi, HEAD tersedia, sumber
  requirement/AC, serta perintah test lokal yang sudah ditinjau.

Contoh shell di panduan ini memakai Linux/macOS. Helper tersedia sebagai Python
CLI; perilaku Windows dan lingkungan enterprise lain belum diuji di fase ini.

## 1. Ambil plugin

```bash
git clone https://github.com/erikgunawan/doforme.git ~/doforme
cd ~/doforme
python3 -B scripts/check_plugin.py
python3 -B scripts/update_docs.py --check
```

Jika GitHub menolak akses, gunakan autentikasi GitHub organisasi Anda atau URL
SSH yang memang sudah diotorisasi. Jangan memasukkan token ke file konfigurasi
plugin, command, issue atau requirement. Tidak ada package/dependency tambahan
yang perlu diinstal untuk pemeriksaan struktur ini.

## 2. Muat dari repo target

```bash
cd /absolute/path/repo-percobaan
claude --plugin-dir "$HOME/doforme" --add-dir "$HOME/doforme/skills"
```

Path plugin harus menunjuk checkout doforme, sedangkan direktori aktif menunjuk
repo yang akan dianalisis. --add-dir memberi akses ke metode/reference plugin di
luar repo target. Jangan menyalin source plugin ke setiap repo target.

Di Claude, periksa `/help` dan `/agents`, lalu jalankan:

```text
/doforme:init
```

Hasil awal yang diharapkan: inspection_only, tidak ada file dibuat, test tidak
dijalankan, dan belum siap fix. Ini adalah pemeriksaan aman untuk mulai mencoba.
Penggunaan lebih lanjut ada di [panduan penggunaan](USAGE.md).

## 3. Opsional: setup repo target

```text
/doforme:init --write
```

Ini hanya membuat `.doforme/repository.json` dan `.doforme/requirements.md` bila
belum ada. Isi requirement adalah draft belum terkonfirmasi, dan test_commands
kosong. Tinjau sumber/AC dan command test sendiri; helper tidak mengesahkannya.
File lama tidak ditimpa. Lihat [onboarding](ONBOARDING.md) untuk konfigurasi lengkap.

Hook pembaruan dokumentasi hanya untuk kontributor repo doforme; pengguna plugin
tidak perlu memasangnya di setiap repo target.

## Update plugin

```bash
git -C "$HOME/doforme" status --short
git -C "$HOME/doforme" pull --ff-only
```

Simpan/review perubahan lokal sebelum update. Restart sesi Claude dengan opsi
plugin yang sama. Baca [history](../CHANGELOG.md) sebelum memakai versi baru.
Checkpoint mengikat policy plugin: perubahan versi/source dapat membuat checkpoint
lama stale. Jangan memaksa resume; lakukan review dan mulai run baru bila diperlukan.

## Pengujian instalasi

```bash
cd ~/doforme
python3 -B scripts/check_plugin.py
python3 -B scripts/update_docs.py --check
python3 -B -m unittest discover -s tests -q
claude plugin validate . --strict
claude plugin validate commands --strict
claude plugin validate agents --strict
claude plugin validate skills --strict
```

Tes unittest bersifat offline dan tidak menggunakan model. Uji model nyata adalah
opt-in berbiaya, memakai repo sementara; baca [runtime acceptance](RUNTIME-0.14.md).
Validasi plugin lokal berbeda dari kelayakan direktori/marketplace: lisensi dan
ikon publikasi belum ditetapkan.

## Pemecahan masalah

| Gejala | Tindakan |
| --- | --- |
| Command doforme tidak terlihat | Pastikan --plugin-dir benar; restart sesi dan periksa /help |
| Skill/reference tidak dapat dibaca | Sertakan --add-dir ke folder skills plugin |
| Helper meminta izin/ditolak | Periksa exact command dan path; jangan menambah bypass atau retry otomatis |
| Repo root tidak valid | Jalankan dari root Git yang dipilih, bukan subfolder/non-Git |
| Doctor blocked | Baca masing-masing blocker; doctor tidak memperbaiki repo otomatis |
| Login/model tidak tersedia | Selesaikan akses Claude/organisasi; doctor hanya mengecek keberadaan CLI |
| Checkpoint stale setelah update | Review konten/policy; gunakan run baru, bukan mengganti hash atau menghapus gate |
| Clone berhasil tetapi issue tidak diproses otomatis | Integrasi issue intake tetap opt-in; lihat INTEGRATIONS.md |

Tidak ada push, publikasi PR atau penutupan issue otomatis oleh workflow plugin.
