# doforme

Plugin Claude Code untuk menyelidiki bug, menyusun rencana berdasarkan requirement,
melakukan fix terbatas, menjalankan pengujian independen, review, dan menyiapkan
draft PR. Tahap-tahapnya dapat dijalankan **manual** atau **end-to-end**.

Requirement dan acceptance criteria (AC) menjadi acuan perilaku yang diharapkan.
Test hijau dan workflow complete tidak otomatis berarti issue sudah diterima
pemilik requirement atau dinyatakan resolved.

Riwayat versi dan perubahan tersedia di [CHANGELOG](CHANGELOG.md).

Plugin doforme tersedia dengan [lisensi MIT](LICENSE).

## Instalasi

Prasyarat: Git, Python 3.9+, dan Claude Code dengan akses model aktif. Runner model
memerlukan lingkungan POSIX. Pasang sekali dengan scope user dari checkout lokal:

```bash
git clone https://github.com/erikgunawan/doforme.git "$HOME/doforme"
claude plugin marketplace add "$HOME/doforme"
claude plugin install doforme@doforme-marketplace --scope user

cd /absolute/path/to/project
claude
```

Gunakan akun GitHub yang memiliki akses ke repo. Direktori aktif adalah repo
project yang akan dianalisis. Instalasi user tersedia untuk semua project pada
komputer ini. Buka sesi Claude baru, lalu periksa `/help` dan `/agents`.
Panggil `/doforme:init` atau `/doforme:analyze`; `/doforme` saja belum tersedia.

Untuk memperbarui checkout yang bersih:

```bash
git -C "$HOME/doforme" pull --ff-only
claude plugin update doforme@doforme-marketplace --scope user
```

Restart sesi Claude setelah memperbarui plugin. Detail prasyarat dan pemecahan
masalah ada di [panduan instalasi](docs/INSTALLATION.md).

### Opsional: template Telegram

**Telegram bukan prasyarat doforme.** Seluruh tahap manual maupun end-to-end
tetap tersedia tanpa bot, chat ID, Secrets/Variables Telegram, atau workflow
notifikasi. Requirement, akses model dan izin eksekusi tetap mengikuti project.

Jika membutuhkan notifikasi, pasang helper dan workflow Telegram di **repo project**,
lalu isi Secrets/Variables di repo tersebut. Ikuti
[langkah instalasi template](docs/INSTALLATION.md#4-opsional-pasang-template-telegram)
dan [panduan konfigurasi Telegram](docs/TELEGRAM.md). Push repo plugin doforme
tidak mengaktifkan notifikasi project.

## Cara pakai

### 1. Siapkan project dan requirement

Dari root Git project, mulai dengan inspeksi tanpa menulis:

```text
/doforme:init
```

Untuk membuat draft konfigurasi awal:

```text
/doforme:init --write
```

Perintah tersebut membuat `.doforme/repository.json` dan
`.doforme/requirements.md` bila belum ada. Isi sumber requirement/AC, konfirmasi
scope yang berlaku, dan perintah test yang sudah ditinjau. Draft generated belum
merupakan requirement yang disetujui. Review dan commit konfigurasi sebelum
memulai workflow yang memerlukan baseline bersih.

Siapkan input issue terpisah, lalu periksa prasyarat lokal:

```text
/doforme:doctor --input /absolute/inputs/issue.json --profile .doforme/repository.json --output /absolute/runs/new-run
```

Doctor tidak menjalankan test/model atau membuat output. Panduan lengkap:
[onboarding](docs/ONBOARDING.md), [contoh requirement](docs/requirement-input.example.md),
dan [pemeriksaan kesiapan](docs/PREFLIGHT.md).

### 2. Jalankan secara manual

```text
/doforme:analyze ISSUE.md; requirement dan konfirmasi scope di REQUIREMENTS.md
/doforme:plan /absolute/reports/ANALYSIS.md
/doforme:fix /absolute/reports/PLAN.md; authorize edits ONLY src/example.py and tests/test_example.py; authorize execution ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v; artifacts none
/doforme:test /absolute/reports/PLAN.md /absolute/reports/FIX.md; authorize execution ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v; artifacts none
/doforme:review /absolute/reports/PLAN.md /absolute/reports/FIX.md /absolute/reports/TEST.md
/doforme:pr /absolute/reports/PLAN.md /absolute/reports/FIX.md /absolute/reports/TEST.md /absolute/reports/REVIEW.md
```

Ganti path dan command contoh sesuai project serta plan yang sudah ditinjau.
Setiap tahap memiliki konteks terpisah: simpan laporan lengkap di luar checkout
atau berikan sebagai inline input lengkap. Nama file laporan di atas adalah
contoh input tahap berikutnya, bukan file yang otomatis disimpan command manual.
Analyze/plan hanya membaca. Fix/test memerlukan izin langsung untuk exact scope.

### 3. Jalankan end-to-end

Input issue memuat issue_ref, issue_text dan exact edit_paths. Profil repo dapat
menyediakan sumber requirement, default test command dan batas eksekusi.
Lihat [contoh konfigurasi](docs/workflow-input.example.json) serta
[aturan penggabungan profil/input](docs/ONBOARDING.md).

Tinjau konfigurasi efektif tanpa menjalankan workflow:

```bash
python3 "$HOME/doforme/scripts/run_workflow.py" --repo /absolute/project --profile .doforme/repository.json --input /absolute/inputs/issue.json --inspect-config
```

Setelah menyetujui scope, jalankan dari Claude:

```text
/doforme:endtoend --input /absolute/inputs/issue.json --profile .doforme/repository.json --output /absolute/runs/new-run; authorize output creation; authorize edits ONLY src/example.py and tests/test_example.py; authorize execution ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v; artifacts none
```

Daftar file/command pada izin langsung harus sesuai input dan kebutuhan project.
Output harus baru dan di luar repo project/plugin. Alur berjalan melalui
analyze → plan → fix → test → review → draft PR, dan berhenti pada prerequisite,
requirement, izin, validation atau review gate yang belum terpenuhi. Model calls
memakai biaya sesuai akun dan batas konfigurasi.

### 4. Lihat status dan lanjutkan run

```text
/doforme:status /absolute/runs/new-run
```

Resume menggunakan input, output dan izin yang sama dengan --resume; retry tahap
blocked/failed memerlukan --retry eksplisit. Perubahan source, HEAD, konfigurasi
atau policy dapat membuat checkpoint stale. Jangan memaksa resume atau menghapus
perubahan parsial tanpa review. Detail ada di [panduan penggunaan](docs/USAGE.md).

### 5. Publikasi dan notifikasi opsional

`/doforme:pr` menyiapkan draft lokal. Publikasi memakai
[helper terpisah dengan izin eksplisit](docs/PUBLISHING.md), sedangkan
[validator acceptance](docs/ACCEPTANCE.md) memeriksa bukti keputusan manusia.

Untuk notifikasi bug baru dan resolved, pasang [konfigurasi Telegram](docs/TELEGRAM.md)
di **repo project**. Pengiriman memerlukan Secrets/Variables dan opt-in operator.
Resolved menurut owner memerlukan bukti/approval yang dijelaskan dalam panduan;
closed atau test hijau saja tidak cukup.

Referensi tambahan: [semua command](docs/REFERENCE.md),
[panduan penggunaan lengkap](docs/USAGE.md), dan
[batas eksekusi/isolasi](docs/OPERATIONS.md).
