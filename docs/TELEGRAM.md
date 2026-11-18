# Konfigurasi repo: bug baru dan resolved → Telegram

Konfigurasi ini dipasang di repo aplikasi target, misalnya sandbox KlikDown.
Ia berlaku untuk fix manual maupun doforme end-to-end. Notifikasi tidak menjalankan
Claude, memperbaiki source, membuat PR, menutup issue atau mengaktifkan hook lab.
API key model tidak diperlukan untuk notifikasi.

**Telegram sepenuhnya opsional.** Repo tanpa workflow ini, tanpa token/chat ID,
atau dengan DOFORME_NOTIFY_TELEGRAM kosong/false tetap dapat memakai semua tahap
doforme manual dan end-to-end. Hanya notifikasi yang tidak dikirim. Credential
Telegram tidak diperlukan oleh init, doctor, analyze, plan, fix, test, review,
draft PR, status atau resume. Ringkasan instalasi ada di
[panduan instalasi plugin](INSTALLATION.md#4-opsional-pasang-template-telegram).

## Definisi status

| Kejadian | Telegram |
| --- | --- |
| Issue baru memiliki label bug, atau label bug ditambahkan pada issue terbuka | Bug baru; belum dinyatakan resolved |
| Test hijau, draft PR, PR belum merge, issue closed tanpa bukti owner | Tidak mengirim klaim resolved |
| Issue closed sebagai completed, PR merge sesuai SHA, check wajib hijau, owner approver memberi deklarasi dan bukti QA/UAT | Resolved menurut persetujuan owner, beserta PR/commit/bukti |
| Issue dibuka kembali | Bukti lama tidak cukup untuk resolved lagi; diperlukan bukti/deklarasi baru |

Sumber keputusan business acceptance adalah deklarasi akun GitHub yang ditunjuk
operator, bukan inferensi AI atau status test. Workflow memverifikasi akun, PR,
SHA, check dan referensi komentar; ia tidak membaca piksel screenshot, membuktikan
kelengkapan seluruh requirement, atau mengautentikasi jabatan bisnis di luar
daftar akun tersebut. Hubungan PR dengan bug serta source/AC dinyatakan owner.
Hasil diberi label owner-attested accepted, bukan acceptance yang dibuktikan AI.

## 1. Pasang tiga file

Jalankan dari root repo KlikDown yang sudah menjadi checkout Git. Gunakan checkout
doforme versi 0.25 atau lebih baru dan review file sebelum menyalinnya:

```bash
DOFORME="$HOME/doforme"
mkdir -p .github/workflows .github/scripts
cp -i "$DOFORME/integrations/telegram_bugs.py" .github/scripts/doforme_telegram.py
cp -i "$DOFORME/integrations/telegram-bugs.yml.example" .github/workflows/doforme-telegram.yml
cp -i "$DOFORME/integrations/klikdown-tests.yml.example" .github/workflows/tests.yml
```

Gunakan path baru atau gabungkan dengan file existing secara sadar; jangan
menimpa workflow/CI milik orang lain. Repo selain KlikDown perlu mengganti command
test sesuai proyek. CI KlikDown ini menjalankan node tests/run-node.js tanpa npm
install dan tanpa secrets. Node tersedia pada runner yang dipilih harus sesuai
persyaratan Node 20+ proyek. Test regresi BUG-303 tetap perlu ditambahkan dan
didaftarkan; baseline hijau saja belum membuktikan rendering benar.

Commit dan push tiga file tersebut ke default branch repo aplikasi. Template di
repo doforme berada di luar workflow aktif, sehingga push doforme tidak mengirim
notifikasi. File workflow issue/comment harus ada di default branch agar event
tersebut diproses. Tidak ada checkout branch PR dalam job pemegang secret Telegram.

## 2. Isi repository secrets

GitHub → repo aplikasi → Settings → Secrets and variables → Actions → Secrets:

| Secret | Nilai |
| --- | --- |
| TELEGRAM_BOT_TOKEN | Token bot milik operator dari BotFather |
| TELEGRAM_CHAT_ID | ID chat/grup tujuan yang operator pilih |

Untuk chat pribadi, buka percakapan dengan bot dan tekan Start. Untuk grup,
tambahkan bot dan pastikan dapat mengirim pesan. Ambil chat ID lewat API/tools
Telegram yang Anda tinjau; hindari menaruh token pada URL browser, screenshot,
issue, file Git atau percakapan publik. Jangan kirim token ke coding agent/chat.
GITHUB_TOKEN disediakan GitHub Actions; tidak perlu membuat PAT untuk workflow ini.

## 3. Isi repository variables

Di halaman Actions yang sama, pilih Variables:

| Variable | Contoh | Fungsi |
| --- | --- | --- |
| DOFORME_NOTIFY_TELEGRAM | true | Opt-in pengiriman; kosong/false berarti disabled |
| DOFORME_BUG_LABEL | bug | Nama label yang harus ada pada issue |
| DOFORME_RESOLUTION_APPROVERS | erikgunawan | Username GitHub yang berwenang menyatakan QA/UAT diterima; pisahkan dengan baris baru atau koma |
| DOFORME_REQUIRED_CHECKS | tests | Nama check job wajib; satu nama per baris |

Daftar approver adalah keputusan operator mengenai authority. Kehadiran secret
saja tidak mengaktifkan pengiriman. Pilih tujuan/akun yang benar dan tinjau
hak baca informasi issue privat sebelum mengaktifkan. Batasi siapa yang boleh
mengubah variables, workflow dan kode notifier sesuai aturan repo Anda.

## 4. Uji notifikasi bug baru

1. Pastikan GitHub Actions diizinkan dan file workflow ada di default branch.
2. Buat issue latihan baru, misalnya BUG-303, dengan label bug. Atau tambahkan
   label bug pada issue yang masih open.
3. Periksa Actions → doforme bug Telegram dan chat tujuan.

Notifikasi memuat repo, nomor issue, judul dan URL. Isi issue tidak dieksekusi
atau dimasukkan ke shell. PR dan komentar pada PR tidak diproses sebagai bug issue.
Issue yang sudah ada sebelum pemasangan tidak otomatis dikirim secara retroaktif.

## 5. Fix manual atau end-to-end, kemudian QA

Gunakan salah satu jalur doforme seperti biasa. Setelah fix/review, commit/push
ke branch, buat PR dan merge melalui keputusan manusia. Gunakan referensi seperti
Refs #1 bila penutupan issue ingin dilakukan setelah QA. Nomor GitHub issue bisa
berbeda dari kode BUG-303 pada judul.

Tunggu job tests pada merge commit/default branch hijau. Owner melakukan QA/UAT
atas merge commit yang tepat, termasuk D6/regression dan pemeriksaan browser
KlikDown. Jangan menganggap BUG-301/302 ikut resolved. Jika ada coverage gap
material, jangan deklarasikan accepted.

## 6. Catat bukti dan keputusan resolved

Approver yang ada dalam variable menulis komentar QA/UAT pada issue tersebut:

```text
QA/UAT BUG-303 pada merge commit <FULL_40_CHARACTER_SHA>:
- D6 dan AC pengurutan: hasil aktual ...
- Regression test: ...
- Browser/screenshot/report: ...
- BUG-301/302 tetap di luar scope; keterbatasan ...
Keputusan acceptance untuk scope yang disebut: accepted.
```

Sertakan SHA lengkap, bukti aktual dan keputusan yang benar; jangan menyalin
placeholder seolah sudah diuji. Salin permalink komentar QA/UAT tersebut.

Kemudian approver membuat **komentar baru** pada issue yang sama dengan format
berikut (hanya fenced block ini). Ganti nomor issue/PR, SHA dan permalink dengan
nilai aktual. Jangan mengedit komentar approval lama; buat komentar baru jika berubah.

````text
```doforme-resolution
{
  "issue": 1,
  "pr": 12,
  "merge_commit": "FULL_40_CHARACTER_SHA",
  "qa": "passed",
  "business_acceptance": "accepted",
  "evidence_url": "https://github.com/OWNER/REPO/issues/1#issuecomment-ACTUAL_ID",
  "source_refs": [
    "docs/rules/dashboard.md:D6",
    "docs/bugs/BUG-303-urutan-deadline-terbalik.md:Kriteria penerimaan"
  ]
}
```
````

Kedua komentar harus berasal dari approver, tidak diedit, setelah PR merge dan
setelah reopen terakhir bila ada. Deklarasi menunjuk PR merged ke default branch,
SHA persis sama, serta komentar bukti pada issue yang sama. Check wajib pada SHA
tersebut harus completed/success dari GitHub Actions.

Tutup issue dengan alasan completed. Jika PR sudah menutup issue otomatis,
komentar deklarasi yang baru dibuat akan memicu pemeriksaan ulang. Setelah semua
gerbang terpenuhi, Telegram menerima status resolved menurut persetujuan owner.

Contoh isi pesan:

```text
✅ Bug resolved — menurut persetujuan owner
OWNER/REPO #1
BUG-303 — urutan deadline terbalik
PR: .../pull/12
Commit: <sha>
Approver: <username>
QA/check wajib: passed; acceptance: owner-attested accepted
Bukti: <permalink QA/UAT>
```

Jika issue terlanjur ditutup sebelum check selesai, gunakan Actions → doforme bug
Telegram → Run workflow → issue_number untuk memeriksa lagi. Ini tetap tidak
melewati bukti/approval atau mengirim ulang attempt yang sudah tercatat.

## Delivery, receipt dan batasnya

Workflow menyimpan artifact attempt **sebelum** menghubungi Telegram, lalu helper
memeriksa ulang state/approval/check sebelum POST. Rerun event yang sama berhenti
jika receipt artifact masih tersimpan; resolved key berbasis closure ID sehingga
komentar tambahan tidak mengirim resolved berulang untuk penutupan yang sama.
Concurrency per issue mencegah dua job pengirim simultan, bukan jaminan urutan FIFO.

Jika timeout/crash terjadi setelah receipt disimpan, delivery bisa belum terjadi
atau sudah terjadi. Workflow tidak retry otomatis. Periksa chat dan artifact
sebelum pemulihan manual. Artifact mengikuti retention repo; menghapus/expired
receipt dapat menghilangkan deduplication. Ini bukan exactly-once delivery permanen.
Perubahan GitHub sesudah recheck terakhir tetap dapat berlomba dengan POST;
pesan mencatat keputusan/commit yang diverifikasi, bukan transaksi atomik lintas layanan.

Notifier hanya membaca metadata GitHub dan POST ke host API Telegram tetap,
tanpa redirect/parse_mode/link previews, instalasi package, source execution,
push, penutupan issue atau komentar bot. Raw issue body/token tidak diarsipkan.
Workflow menjalankan helper standalone dalam Python isolated mode (-I -B),
sehingga module shadowing dari project/PYTHONPATH tidak dimuat. Helper dari
default branch tetap harus merupakan kode yang ditinjau operator.
Identity/authority korporat, kebenaran semantik UAT dan kebutuhan deployment
tetap tanggung jawab proses owner; labels/test hijau tidak menggantikannya.

## Status implementasi

Konfigurasi/template dan unit tests tersedia, tetapi belum dipasang pada repo
KlikDown atau dikirim ke chat nyata: repo target, token dan recipient belum
disediakan. Pengujian memakai API/sender palsu dan tidak mengklaim live delivery.
Notifikasi default legacy issue_intake.py tetap terpisah dan hanya new-issue;
gunakan template ini jika membutuhkan gerbang resolved yang didokumentasikan.

Referensi resmi: [event issue/comment](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
[check runs](https://docs.github.com/en/rest/checks/runs),
[artifact metadata](https://docs.github.com/en/rest/actions/artifacts),
dan [Telegram sendMessage](https://core.telegram.org/bots/api#sendmessage).
