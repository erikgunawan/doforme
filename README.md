# doforme

Plugin Claude Code untuk menyelidiki bug, menyusun rencana berdasarkan requirement,
memperbaiki source dalam scope yang disetujui, menguji hasil, melakukan review,
dan menyiapkan draft PR. Bisa dijalankan per tahap atau end-to-end.

Mulai dengan command singkat. doforme memandu setup, menemukan tiket, menyimpan
laporan per issue, dan meminta konfirmasi hanya untuk keputusan yang diperlukan.

[Cara kerja dan diagram alur](docs/HOW-IT-WORKS.md) ·
[Panduan penggunaan mudah](docs/GUIDED-USAGE.md) · [CHANGELOG](CHANGELOG.md)

## Instalasi

Prasyarat: Git, Python 3.9+, dan Claude Code dengan akses model aktif. Runner
memakai lingkungan POSIX. Install sekali untuk seluruh project di komputer ini:

```bash
git clone https://github.com/erikgunawan/doforme.git "$HOME/doforme"
claude plugin marketplace add "$HOME/doforme"
claude plugin install doforme@doforme-marketplace --scope user
```

Buka sesi baru dari repo project:

```bash
cd /absolute/path/to/project
claude
```

Untuk update checkout yang bersih:

```bash
git -C "$HOME/doforme" pull --ff-only
claude plugin update doforme@doforme-marketplace --scope user
```

Buka ulang sesi Claude setelah update. Detail dan pemecahan masalah tersedia di
[panduan instalasi](docs/INSTALLATION.md).

## Cara pakai

Setup terpandu, tanpa harus menulis prompt panjang:

```text
/doforme:init
```

doforme menemukan sumber requirement dan kandidat test, lalu menunjukkan usulan
konfigurasi. Tinjau AC dan jawab pertanyaan singkat sebelum menyimpan. Commit
konfigurasi yang telah disetujui sebelum memulai run dengan baseline bersih.

Jalankan tahap demi tahap berdasarkan identitas issue:

```text
/doforme:analyze BUG-301
/doforme:plan BUG-301
/doforme:fix BUG-301
/doforme:test BUG-301
/doforme:review BUG-301
/doforme:pr BUG-301
```

Atau gunakan alur end-to-end:

```text
/doforme:endtoend BUG-301
```

ID lokal mencari satu tiket di docs/bugs. Issue GitHub bisa dipilih dengan `#3`
atau URL issue pada remote origin repo; akses GitHub CLI diperlukan. Tanpa
argumen, doforme membantu memilih issue. Laporan disimpan di lokasi privat di
luar checkout; Anda tidak perlu menyalin laporan atau membuat input JSON.

Sebelum fix, doforme menampilkan file yang akan diubah, command test, serta
artefak sementara, lalu meminta persetujuan. End-to-end dapat berhenti setelah
plan untuk meminta persetujuan tersebut. Prasyarat yang kurang dijelaskan dengan
langkah berikutnya; doforme tidak melewati gate agar run terlihat berhasil.

```text
/doforme:status BUG-301
```

Untuk memulai ulang issue yang sama, minta run baru dengan `--new`. Laporan run
lama dipertahankan. Mode advanced dengan input/path dan izin eksplisit tetap
tersedia di [panduan lengkap](docs/USAGE.md) dan [referensi command](docs/REFERENCE.md).

Requirement dan AC menentukan perilaku yang diharapkan. Test hijau dan workflow
complete berarti hasil teknis pada scope yang diuji; penerimaan bisnis tetap
memerlukan keputusan pemilik requirement. PR yang dihasilkan adalah draft lokal.
Publikasi, merge, serta penutupan issue mengikuti izin dan proses project.

### Opsional: Telegram

Telegram bukan prasyarat plugin. Untuk notifikasi bug baru dan resolved, pasang
[template di repo project](docs/INSTALLATION.md#4-opsional-pasang-template-telegram)
dan ikuti [panduan Telegram](docs/TELEGRAM.md). Notifikasi issue baru tidak otomatis
menjalankan doforme. Resolved memerlukan bukti dan deklarasi owner yang berlaku.

## Lisensi

[MIT](LICENSE), copyright 2026 Erik Gunawan. Penggunaan, modifikasi, dan distribusi,
termasuk komersial, diizinkan dengan menyertakan pemberitahuan copyright dan
lisensi. Software disediakan tanpa jaminan.
