# Instalasi doforme

doforme adalah plugin Claude Code. Marketplace lokal mendukung instalasi permanen
dengan scope user dari checkout GitHub. Penggunaan lokal tidak memerlukan GitHub Actions,
Jira, Figma atau Telegram.

## Prasyarat

- Git dan Python 3.9 atau lebih baru. Helper memakai Python standard library.
- Claude Code dengan akun/model yang dapat digunakan. Validasi struktur CLI terbaru: 2.1.327; uji interaktif terpandu dilaporkan terpisah.
- Hak baca ke repo GitHub doforme dan repo target yang ingin diperiksa.
- Untuk workflow fix: Git checkout kecil yang terisolasi, HEAD tersedia, sumber
  requirement/AC, serta perintah test lokal yang sudah ditinjau.

Contoh shell di panduan ini memakai Linux/macOS. Helper tersedia sebagai Python
CLI; perilaku Windows dan lingkungan enterprise lain belum diuji di fase ini.
Runner model memakai proses/pipe POSIX; backend isolasi OS harus ditinjau dan
divalidasi terpisah sesuai [panduan operasional](OPERATIONS.md).

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

## 2. Pasang sekali, gunakan dari sesi biasa

Daftarkan marketplace lokal, lalu install untuk pengguna komputer ini:

```bash
claude plugin validate "$HOME/doforme"
claude plugin marketplace add "$HOME/doforme"
claude plugin install doforme@doforme-marketplace --scope user
claude plugin list
```

Sesuaikan path bila checkout bukan di ~/doforme. Scope user membuat plugin
tersedia di semua repo pada komputer ini; tidak perlu menyalin plugin atau
mengubah konfigurasi Claude setiap repo. Pada CLI 2.1.327 yang diuji, instalasi
marketplace lokal membaca langsung checkout (readFromFolder). Biarkan checkout
tersedia dan review perubahan lokal sebelum membuka sesi baru. Versi CLI lain
dapat memakai salinan cache.

Buka sesi Claude Code baru dari repo target:

```bash
cd /absolute/path/repo-percobaan
claude
```

Gunakan `/doforme:init` atau `/doforme:analyze`, bukan `/doforme` saja. Jika sesi
lama belum menampilkan command, tutup dan buka kembali. Izin tools tetap mengikuti
Claude Code dan project; konfirmasi akses yang diminta saat membaca resource plugin.

### Alternatif untuk pengembangan: muat hanya satu sesi

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

Hasil awal: inspeksi repo dan pertanyaan singkat tentang konfigurasi yang diusulkan.
Default init kini terpandu; ia tidak menulis sebelum persetujuan proposal. Untuk
inspeksi helper lama tanpa percakapan setup, gunakan `/doforme:init --inspect`.
Lanjutkan dengan [panduan command singkat](GUIDED-USAGE.md).
`/doforme:doctor` memeriksa kesiapan repo tanpa memilih tiket; `/doforme:status`
menampilkan run tersimpan. Pilihan issue mengutamakan GitHub origin dan selalu
menampilkan sumber GitHub/Lokal.

## 3. Setup terpandu atau draft advanced

Mode terpandu `/doforme:init` membaca kandidat sumber/test dan meminta keputusan
AC serta persetujuan menyimpan konfigurasi. Untuk membuat template kosong saja:

```text
/doforme:init --write
```

Ini hanya membuat `.doforme/repository.json` dan `.doforme/requirements.md` bila
belum ada. Isi requirement adalah draft belum terkonfirmasi, dan test_commands
kosong. Tinjau sumber/AC dan command test sendiri; helper tidak mengesahkannya.
File lama tidak ditimpa. Lihat [onboarding](ONBOARDING.md) untuk konfigurasi lengkap.

Hook pembaruan dokumentasi hanya untuk kontributor repo doforme; pengguna plugin
tidak perlu memasangnya di setiap repo target.

## 4. Opsional: pasang template Telegram

Lewati seluruh bagian ini jika tidak memerlukan notifikasi. Analyze, plan, fix,
test, review, draft PR, status dan end-to-end tidak bergantung pada Telegram.
Token/chat ID yang belum dikonfigurasi bukan blocker untuk workflow plugin lokal.

Template dipasang di repo aplikasi target, bukan di repo plugin. Dari root
project, salin dua file berikut dari checkout doforme yang sudah diperbarui:

```bash
DOFORME="$HOME/doforme"
cd /absolute/path/to/project
mkdir -p .github/workflows .github/scripts
cp -i "$DOFORME/integrations/telegram_bugs.py" .github/scripts/doforme_telegram.py
cp -i "$DOFORME/integrations/telegram-bugs.yml.example" .github/workflows/doforme-telegram.yml
```

Opsi -i meminta konfirmasi sebelum menimpa file; review dan gabungkan jika project
sudah memiliki konfigurasi serupa. Project dengan CI existing tetap memakai test
dan check yang sesuai project tersebut. Khusus lab KlikDown yang belum memiliki
CI, template tambahan tersedia di integrations/klikdown-tests.yml.example:

```bash
cp -i "$DOFORME/integrations/klikdown-tests.yml.example" .github/workflows/tests.yml
```

Jangan memakai command test KlikDown untuk project dengan stack berbeda. Setelah
meninjau file, commit dan push konfigurasi ke default branch **repo project**.

Di Settings → Secrets and variables → Actions repo project, isi:

| Jenis | Nama | Isi |
| --- | --- | --- |
| Secret | TELEGRAM_BOT_TOKEN | Token bot yang dipilih operator |
| Secret | TELEGRAM_CHAT_ID | Chat/grup tujuan |
| Variable | DOFORME_NOTIFY_TELEGRAM | false selama setup; true setelah siap mengirim |
| Variable | DOFORME_BUG_LABEL | bug, atau label pilihan project |
| Variable | DOFORME_RESOLUTION_APPROVERS | Akun GitHub approver yang ditunjuk operator |
| Variable | DOFORME_REQUIRED_CHECKS | Nama check CI wajib, satu per baris; contoh tests |

Isi token langsung di GitHub Secrets, bukan di source, issue atau chat. Bot harus
bisa mengirim ke chat yang dipilih. API key model tidak diperlukan oleh notifier;
akses model tetap diperlukan bila menjalankan workflow doforme.

Sesudah konfigurasi lengkap, ubah DOFORME_NOTIFY_TELEGRAM menjadi true dan uji
dengan issue latihan baru berlabel bug. Notifikasi resolved baru dikirim setelah
PR merge, check pada commit terkait lulus, bukti/deklarasi approver tersedia dan
issue closed/completed. Ikuti format dan gerbang di [panduan Telegram](TELEGRAM.md).
Template tidak menjalankan auto-fix, membuat PR atau menutup issue sendiri.

Jika workflow Telegram tidak dipasang, flag kosong/false, atau pengiriman gagal,
fungsi plugin manual/end-to-end tetap tersedia. Masalah delivery ditangani pada
workflow notifikasi di GitHub Actions; itu terpisah dari hasil run plugin lokal.

## Update plugin

Jika memakai arsip kandidat, baca [cara memverifikasi kandidat](RELEASE-CANDIDATE.md)
dan pilih commit/provenance melalui jalur yang Anda percayai. Hash mendeteksi
perubahan terhadap manifest yang diberikan; bukan tanda tangan owner atau bukti
kesiapan stable. [Status roadmap](ROADMAP.md) mencatat gate live yang masih pending.

```bash
git -C "$HOME/doforme" status --short
git -C "$HOME/doforme" pull --ff-only
```

Untuk instalasi permanen, minta Claude memperbarui instalasi setelah pull:

```bash
claude plugin update doforme@doforme-marketplace --scope user
```

Simpan/review perubahan lokal sebelum update. Restart sesi Claude sesudahnya.
Mode --plugin-dir langsung memakai checkout dan tidak memerlukan plugin update.
Baca [history](../CHANGELOG.md) sebelum memakai versi baru.
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
Uji workflow dengan profil, status dan resume dijelaskan di [workflow acceptance](RUNTIME-0.16.md).
Uji slash endtoend langsung tersedia di [slash acceptance](RUNTIME-0.17.md).
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
