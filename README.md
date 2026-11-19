# doforme

**Dari laporan bug ke draft PR, lengkap dengan bukti di setiap langkah.**

doforme adalah plugin Claude Code yang membantu tim menyelidiki bug, merencanakan
perbaikan, mengubah kode dalam scope yang disetujui, dan memverifikasi hasilnya.
Satu alur kerja menghubungkan issue, requirement, pengujian, dan review—dengan
keputusan penting tetap di tangan Anda.

[Panduan instalasi dan penggunaan](docs/GETTING-STARTED.md) ·
[Cara kerja dan diagram alur](docs/HOW-IT-WORKS.md)

## Fitur

### Mulai dengan percakapan, bukan prompt panjang

Setup terpandu menemukan sumber requirement dan kandidat test di repo, lalu
membantu Anda meninjau AC dan konfigurasi melalui pertanyaan singkat. Tidak perlu
merangkai input JSON atau menyalin laporan antar-tahap pada mode terpandu.

### Kerjakan issue dari GitHub atau tiket lokal

Pemilihan issue mengutamakan GitHub saat repo memiliki GitHub origin. Setiap tiket
menampilkan sumbernya dengan jelas. Tiket lokal tersedia untuk lab dan alur offline.

### Investigasi dengan evidence yang bisa ditelusuri

Analisis memisahkan fakta, dugaan pelapor, dan hipotesis penyebab. Laporan memuat
validitas issue, lokasi evidence, tingkat keyakinan, serta langkah berikutnya.
Investigasi awal membaca source tanpa mengubah kode atau menjalankan test.

### Perbaikan berpijak pada requirement bisnis

Gunakan spesifikasi repo, dokumen bisnis, atau ekspor requirement Jira/Figma
sebagai acuan yang dikonfirmasi berlaku. AC menghubungkan perilaku yang diharapkan
dengan rencana perbaikan dan bukti pengujiannya. Jika ada ambiguitas, doforme
memandu konfirmasi sebelum melanjutkan.

### Enam tahap, satu alur yang terhubung

Analyze → Plan → Fix → Test → Review → Draft PR. Peran spesialis menangani setiap
tahap, dengan pemeriksaan hasil sebelum diteruskan ke tahap berikutnya. Jalankan per tahap untuk meninjau
setiap keputusan, atau gunakan end-to-end dengan persetujuan scope setelah plan.

### Kontrol perubahan sebelum kode disentuh

Lihat file yang akan diubah, perintah pengujian, dan artefak sementara sebelum memberi
persetujuan. Pengujian independen dan review memeriksa hasil terhadap scope serta
evidence. Draft PR merangkum pekerjaan untuk ditinjau sebelum publikasi.

### Laporan tersimpan, progres mudah dilihat

Laporan dan checkpoint disimpan otomatis per issue di luar checkout. Periksa
kesiapan repo, lihat run yang tersimpan, dan lanjutkan tahap tanpa kehilangan
konteks. Run baru mempertahankan laporan sebelumnya untuk ditinjau kembali.

### Notifikasi Telegram untuk lifecycle bug

Integrasi opsional pada repo project mengirim notifikasi bug baru dan resolved
menurut persetujuan owner. Bukti PR merge, check wajib, dan keputusan QA/UAT
menghubungkan notifikasi resolved dengan perubahan yang relevan.

[Mulai menggunakan doforme](docs/GETTING-STARTED.md) ·
[Riwayat perubahan](CHANGELOG.md) · [Lisensi MIT](LICENSE)
