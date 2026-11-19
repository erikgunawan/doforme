# Instalasi dan penggunaan doforme

Panduan ini membantu Anda memasang plugin, menyiapkan repo, dan menangani issue
pertama. Detail percakapan dan kondisi berhenti ada di [panduan terpandu](GUIDED-USAGE.md).

## 1. Instalasi sekali untuk semua project

Siapkan Git, Python 3.9+, dan Claude Code dengan akses model aktif. Runner memakai
lingkungan POSIX. Untuk membaca issue GitHub, siapkan GitHub CLI (`gh`) dengan
akses ke repo project. Model calls memakai biaya sesuai akun dan batas run.

```bash
git clone https://github.com/erikgunawan/doforme.git "$HOME/doforme"
claude plugin marketplace add "$HOME/doforme"
claude plugin install doforme@doforme-marketplace --scope user
```

Gunakan akun GitHub yang memiliki akses ke repo. Buka sesi baru dari project:

```bash
cd /absolute/path/to/project
claude
```

Plugin tersedia pada scope user; tidak perlu menambahkan flag plugin setiap
membuka sesi. Sesuaikan path jika checkout plugin bukan di ~/doforme.
Detail prasyarat dan pemecahan masalah ada di [panduan instalasi](INSTALLATION.md).

## 2. Siapkan repo

```text
/doforme:doctor
/doforme:init
```

Doctor memeriksa kesiapan repo tanpa meminta tiket. Init membaca kandidat sumber
requirement dan kode test, mengajukan konfirmasi AC yang relevan, lalu menunjukkan
perubahan konfigurasi sebelum meminta persetujuan menyimpannya.

Review dan commit konfigurasi yang telah disetujui sebelum memulai run dengan
baseline bersih. Setup tidak otomatis melakukan pull, commit, push, atau
menjalankan test. Temuan script bukan izin untuk mengeksekusinya.

## 3. Pilih issue dan cara kerja

Untuk memilih issue GitHub yang tersedia:

```text
/doforme:analyze
```

Issue GitHub pada origin repo ditawarkan terlebih dahulu, dengan label sumber
yang jelas. Anda dapat memasukkan nomor/URL langsung atau memilih tiket lokal.

Contoh perintah berikut memakai GitHub issue #3. Ganti dengan nomor sebenarnya:

```text
/doforme:analyze #3
/doforme:plan #3
/doforme:fix #3
/doforme:test #3
/doforme:review #3
/doforme:pr #3
```

Gunakan identitas issue yang sama antar-tahap. Untuk tiket lokal, contoh ID-nya
BUG-301, yang mencari satu file di docs/bugs. ID lokal tidak otomatis dipetakan ke
nomor GitHub. Laporan mode terpandu tersimpan otomatis di luar checkout.

Untuk menjalankan alur end-to-end:

```text
/doforme:endtoend #3
```

Doforme dapat berjalan sampai plan terlebih dahulu, lalu menunjukkan file edit,
command test, serta artefak yang direncanakan. Konfirmasi Anda diperlukan sebelum
perubahan atau eksekusi sesuai scope tersebut. Requirement yang belum jelas atau
bukti yang kurang dapat menghentikan run dan memunculkan pertanyaan lanjutan.

## 4. Lihat progres atau mulai run baru

```text
/doforme:status
/doforme:status #3
/doforme:analyze #3 --new
```

Status tanpa ID menampilkan run yang tersimpan pada checkout ini. Status per issue
memeriksa run tersebut. Run baru mempertahankan laporan sebelumnya dan tidak
mewarisi izin edit run lama. Perubahan requirement, source, atau policy plugin
dapat mengharuskan sesi analisis baru.

Jika terblokir, baca alasan dan jawab pertanyaan yang relevan. Jangan mengubah
laporan atau memaksa resume untuk mendapatkan verdict yang berbeda. Lihat
[panduan terpandu](GUIDED-USAGE.md) untuk retry dan persetujuan scope, atau
[panduan advanced](USAGE.md) untuk input serta path eksplisit.

## 5. Review, acceptance, dan notifikasi

Hasil PR stage adalah draft lokal. Publikasi, review manusia, CI, QA/UAT, merge,
dan penutupan issue mengikuti izin serta proses project. Test hijau dan workflow
complete menunjukkan hasil teknis pada scope yang diuji; pemilik requirement
tetap menentukan penerimaan bisnis.

Jika memerlukan notifikasi, ikuti [instalasi template Telegram](INSTALLATION.md#4-opsional-pasang-template-telegram)
di repo project dan [konfigurasi lifecycle Telegram](TELEGRAM.md). Telegram tidak
wajib untuk menggunakan plugin. Notifikasi issue baru tidak otomatis menjalankan
Claude atau memperbaiki source.

## Update plugin

Dari checkout plugin yang bersih:

```bash
git -C "$HOME/doforme" pull --ff-only
claude plugin update doforme@doforme-marketplace --scope user
```

Buka ulang sesi Claude setelah update. Baca [CHANGELOG](../CHANGELOG.md) untuk
riwayat perubahan. Untuk memahami batas eksekusi dan isolasi, baca
[panduan operasional](OPERATIONS.md). Plugin memakai [lisensi MIT](../LICENSE).
