# Dokumentasi dan history pada setiap perubahan

Aturan ini berlaku untuk pengembangan repo doforme, bukan semua repo yang memakai
plugin. File [AGENTS.md](AGENTS.md) juga meminta coding agent mengikuti alur ini.

## Aktifkan pembaruan otomatis sekali per clone

```bash
cd /absolute/path/to/doforme
python3 -B scripts/install_doc_hooks.py --install
```

Installer hanya mengatur core.hooksPath lokal ke .githooks. Ia berhenti bila ada
hooksPath lain atau hook pre-commit existing, agar konfigurasi Anda tidak tertimpa.
Untuk hook manager yang sudah ada, tambahkan invocation berikut pada pre-commit
yang Anda kelola, tanpa mengganti hook lain:

```bash
python3 -B scripts/update_docs.py --sync
python3 -B scripts/update_docs.py --check
```

Git tidak mengaktifkan hook dari clone secara otomatis; setiap clone kontributor
perlu langkah setup ini. Tidak diperlukan login model atau dependency tambahan.

## Setiap perubahan

1. Ubah implementasi dan panduan yang terdampak. Instalasi di docs/INSTALLATION.md,
   alur pengguna di docs/USAGE.md, dan hasil pengujian di docs/PHASES.md.
2. Stage hanya perubahan yang Anda maksud. Hook tidak men-stage source lain.
3. Opsional: tulis ringkasan bermakna sebelum commit:

```bash
python3 -B scripts/update_docs.py --sync --summary "Jelaskan perubahan dan akibatnya bagi pengguna"
```

4. Jalankan pemeriksaan, lalu commit seperti biasa:

```bash
python3 -B scripts/update_docs.py --check
python3 -B scripts/check_plugin.py
python3 -B -m unittest discover -s tests -q
git commit -m "Jelaskan perubahan"
```

Pre-commit otomatis memperbarui dan men-stage hanya tiga file yang dikelola:

| File | Sumber kebenaran | Cara diperbarui |
| --- | --- | --- |
| docs/changes.json | File yang di-stage, Git blob/mode, parent revision, tanggal Jakarta, versi plugin | Tambah entri per perubahan commit |
| CHANGELOG.md | docs/changes.json | Render ulang riwayat yang dapat dibaca |
| docs/REFERENCE.md | Manifest dan frontmatter command yang di-stage | Render ulang versi/command/agent/input |

Jika --summary tidak diberikan, history memakai daftar file yang berubah, bukan
menebak perilaku fitur atau mengambil commit message yang belum tersedia saat
pre-commit. Ringkasan eksplisit tetap dipakai ketika hook menyegarkan entri yang
sama. Review ringkasan itu bila scope berubah. Mengulang updater sebelum commit
menyegarkan entri pending, bukan membuat duplikat.

Tidak ada file generated yang perlu diedit manual. Updater menolak menimpa edit
lokal yang belum di-stage pada file managed; review perubahan tersebut terlebih
dahulu. Entri committed lama dipertahankan. Perubahan working tree pada source
yang belum di-stage tidak dimasukkan ke history dan tidak ditimpa. Untuk dokumen
naratif, pembaruan tetap tanggung jawab penulis/reviewer: generator tidak dapat
mengetahui apakah deskripsi requirement atau instruksi baru sudah benar.

## GitHub dan pemeriksaan anti-stale

Workflow `.github/workflows/documentation.yml` disiapkan untuk push, pull request
dan workflow_dispatch. Ia baru berjalan di GitHub setelah file workflow dipush
dan Actions diizinkan pada repo. Job memakai contents:read, tidak memakai model/
secret eksternal, tidak membuat commit bot, dan tidak memproses issue.

Pemeriksaan memastikan generated docs sinkron, riwayat lama tidak ditulis ulang,
dan file yang berubah antara base dan head tercakup entri history baru dengan
Git blob/mode terkini. Dengan demikian mencentang nama file saja tidak cukup jika
isinya berbeda. Rename dicatat sebagai delete/add. Pada push banyak commit,
squash atau merge, coverage diperiksa untuk perubahan bersih base → head; ini
bukan bukti bahwa setiap intermediate commit memiliki dokumentasi sempurna.

```bash
python3 -B scripts/update_docs.py --check --base origin/master
```

Pemeriksaan ini tidak dapat memblokir push yang sudah terjadi. Owner perlu
menjadikan job `Documentation and history / documentation` sebagai required
status check di aturan branch bila ingin mencegah merge saat gagal. Hook dapat
dilewati oleh Git, sehingga CI merupakan pemeriksaan tambahan, bukan jaminan
anti-tamper terhadap pihak yang mengubah pemeriksa/workflow itu sendiri.

Konflik history dari dua branch perlu menggabungkan entri sambil mempertahankan
prefix committed dari base. Setelah menyelesaikan konflik kode, stage resolusi
dan jalankan updater agar identitas konten akhir tercatat. Jangan menghapus
riwayat lama untuk meloloskan check. CI tidak melakukan perbaikan diam-diam.

## History awal dan versi

History awal diimpor dari commit Git yang sudah ada, termasuk subject, versi
manifest dan file yang berubah; rekonstruksi fase 0.2/0.3 tetap memiliki batas
sebagaimana dijelaskan di docs/PHASES.md. Import tidak menciptakan klaim tes baru.
--bootstrap hanya untuk setup awal ketika docs/changes.json belum ada. Checkout
normal tidak perlu mengulangnya. Versi tidak otomatis dinaikkan dan tag/release
GitHub tidak dibuat oleh updater.

Referensi upstream: [Git hooks](https://git-scm.com/docs/githooks) dan
[workflow permissions/events](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
