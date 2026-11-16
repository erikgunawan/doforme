# Snapshot sumber requirement — fondasi fase 20

Helper ini mengimpor ekspor teks yang dipilih secara eksplisit dari dokumen bisnis,
Jira, Figma, spec repo atau konfirmasi pengguna. Ia menyimpan konten asli beserta
provenance dan hash tanpa mengubah source. Tidak ada pengambilan URL, koneksi akun,
model call, eksekusi source, konfirmasi requirement otomatis atau validasi visual.

Fase integrasi sumber live belum selesai: URL dokumen/tiket/frame yang benar,
hak akses, kebutuhan sumber pilot dan akun layanan belum diberikan. Helper lokal
ini adalah fondasi yang bisa dipakai sekarang; jangan menyebutnya integrasi
Jira/Figma/Docs live yang sudah berhasil.

## Manifest eksplisit

Simpan ekspor sebagai file teks UTF-8 biasa di repo target. Manifest dapat berada
di luar checkout, misalnya `/absolute/inputs/sources.json`:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "source_id": "S1",
      "kind": "jira",
      "path": "requirements/BUG-123-export.md",
      "origin": "https://example.atlassian.net/browse/BUG-123",
      "origin_locator": "description dan acceptance criteria",
      "version": "export yang diberikan owner; updated time belum diverifikasi",
      "source_accessed_at": "unknown"
    }
  ]
}
```

Kind yang didukung: business_document, jira, figma, repository_spec dan
user_confirmation. origin dan origin_locator adalah metadata yang diberikan
pemanggil, bukan bukti bahwa helper membaca sistem remote. version yang tidak
diberikan tetap unknown. source_accessed_at opsional menerima waktu ISO dengan
timezone yang disediakan pemanggil; helper tidak mengarang waktu akses remote.

```bash
python3 -B /absolute/doforme/scripts/requirement_sources.py --repo /absolute/target --manifest /absolute/inputs/sources.json --output /absolute/snapshots/bug-123
```

Repo harus root Git yang dipilih. Output harus direktori baru di luar target
dan checkout plugin, dengan parent yang sudah ada. Output menggunakan mode 700,
file mode 600; file existing tidak ditimpa. Satu kegagalan menulis dapat meninggalkan
snapshot parsial, yang dilaporkan untuk review manual, bukan dihapus diam-diam.

## Isi hasil

- S1.txt, S2.txt, dan seterusnya: byte UTF-8 ekspor yang dibaca, tanpa perubahan.
- sources.json: origin, locator yang diberikan, lokasi lokal/line range yang
  benar-benar dibaca, version, SHA-256, byte length dan timestamp import UTC.
- authority selalu unconfirmed, freshness unknown, requirements_status
  needs_information, business_acceptance not_evaluated dan remote_actions none.

Timestamp import berbeda dari waktu akses atau pembaruan sumber remote. Hash
mendeteksi perubahan byte snapshot, bukan membuktikan identitas owner, keaslian
ekspor atau versi remote terbaru. Teks berisi perintah tetap data tidak tepercaya
dan tidak pernah dieksekusi. Jenis sumber user_confirmation tidak otomatis
mengautentikasi identitas pemilik requirement.

Review sumber dan metadata bersama-sama sebelum menempatkan salinan yang
disetujui di repo target untuk konfigurasi requirements. Helper tidak mengedit
profil, memasukkan sumber otomatis, men-stage file atau melakukan commit. Bukti
owner applicability, konflik dan AC tetap harus diberikan serta diperiksa pada
analyze/plan. Snapshot ekspor bukan bukti penerimaan implementasi.

## Batas dan pemeriksaan

Manifest dibatasi 1 MB, sumber 1 MB per file, total 4 MB dan maksimal 16 sumber.
Source ID dan canonical path harus unik. File harus reguler, non-symlink dan teks
UTF-8 nonempty; traversal, sumber credential, FIFO/special file, key JSON duplikat,
field pemberi authority, serta origin URL bercredential ditolak. Tidak ada source
precedence otomatis antara dokumen, Jira dan Figma. Figma yang diimpor sebagai
teks hanya mendukung klaim tekstual; pixel, layout dan interaksi visual belum diuji.

Validasi lokal memakai repo Git sementara dan ekspor sintetis, mencakup byte/hash,
schema, scope, permission, special file, partial failure dan CLI nyata. Pengujian
ini tidak menghubungi Jira, Figma, Google Docs atau GitHub dan tidak membuktikan
integrasi akun atau bisnis live.
