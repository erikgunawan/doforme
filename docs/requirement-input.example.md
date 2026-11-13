# Contoh paket input requirement

Ini template, bukan requirement atau persetujuan bisnis yang sudah diverifikasi.
Isi bagian relevan dengan data nyata; tandai yang belum diketahui secara jelas.
Simpan paket di repo target atau berikan sebagai kutipan inline, lalu sebutkan
paket tersebut dalam input analyze. Jangan sertakan credentials atau data pribadi.

## Identitas dan scope

- Issue: <key/link/path issue>
- Scope: <perilaku yang diperiksa, termasuk pengecualian>
- Pemilik requirement: <peran atau identitas owner yang relevan>
- Konfirmasi sumber berlaku untuk scope ini: <kutipan dan referensi konfirmasi,
  atau unconfirmed; jangan isi seolah sudah disetujui>

## Sumber dokumen bisnis

- Origin: <URL/ID, judul, bagian>
- Versi / updated time: <diketahui atau unknown>
- Provenance: <ekspor snapshot atau kutipan; siapa/kapan jika diketahui>
- Isi relevan: <teks aturan bisnis, batas, perhitungan, pengecualian>

## Sumber Jira — bila relevan

- Origin: <key tiket, URL, bagian atau komentar spesifik>
- Versi / updated time: <diketahui atau unknown>
- Isi relevan: <scope issue dan acceptance criteria yang benar-benar tertulis>
- Klarifikasi/keputusan owner: <kutipan dan referensi atau unconfirmed>

## Sumber Figma — bila relevan

- Origin: <file URL, frame/node ID, versi bila diketahui>
- Isi anotasi: <state, interaksi, kondisi, atau teks yang benar-benar diberikan>
- Evidence visual: <tersedia/tidak; jangan mengklaim layout sudah diperiksa dari teks>
- Scope yang belum terjelaskan: <state error/loading/empty, ukuran layar, dll.>

## Acceptance criteria

| ID | Requirement / sumber | Kondisi/input | Hasil teramati | Explicit/proposed | Referensi konfirmasi |
| --- | --- | --- | --- | --- | --- |
| AC1 | <aturan dan locator> | <kondisi> | <hasil> | <basis> | <referensi atau unconfirmed> |

## Konflik dan pertanyaan

- <Pernyataan sumber A dibanding sumber B; dampak; keputusan yang dibutuhkan>
- <Interpretasi yang masih usulan; siapa yang perlu mengonfirmasi>

Sumber yang tidak tersedia: <mana yang material dan mengapa; opsional bila scope
sudah ditutup sumber lain yang terkonfirmasi>. Tidak perlu mengisi sumber yang
tidak relevan. Konfirmasi scope tidak sama dengan penerimaan hasil fix.
