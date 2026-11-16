# Bukti penerimaan bisnis eksplisit

Workflow complete, test hijau dan review pass adalah bukti teknis, bukan
persetujuan pemilik bisnis. Utility ini memeriksa artifact keputusan manusia
terpisah dan mengikatnya pada konten yang benar-benar diuji. Ia tidak mengubah
checkpoint, menutup issue, memublikasikan PR atau memberi izin eksekusi.

## 1. Siapkan workflow dan daftar AC yang ditinjau

Gunakan checkpoint complete/fresh dengan review pass. Semua report, input dan
bukti test tetap harus lolos verifikasi integritas runner. Setelah perubahan
source/requirement/revisi/policy, acceptance lama tidak boleh dipakai kembali.

Siapkan file criteria JSON di lokasi yang dipilih eksplisit. Berikut hanya contoh
sintetis; statement harus berupa kutipan persis dari source requirement workflow:

```json
{
  "contract_version": 1,
  "criteria": [
    {
      "id": "AC1",
      "statement": "Expected first result.",
      "source_path": ".doforme/requirements.md",
      "confirmation_reference": "Referensi keputusan owner bahwa AC ini berlaku untuk issue"
    }
  ]
}
```

Sertakan tepat semua AC ID kanonis seperti AC1/AC2 yang disebut pada report
plan/test/review. Locator source yang didukung adalah tepat satu definisi satu
baris `AC1: statement lengkap` (opsional bullet `- AC1: ...` atau `* AC1: ...`).
Field statement harus sama persis dengan isi setelah colon pada **entri ID yang
sama**, bukan sekadar teks yang terdapat di bagian lain file. Dengan demikian
statement AC2 tidak dapat dipasangkan ke AC1. Entri duplikat, tabel, label bold,
definisi multiline atau layout ambigu ditolak, bukan ditebak. Pisahkan narasi
berikutnya dengan baris kosong; definisi AC berikutnya boleh langsung mengikuti
baris sebelumnya. Siapkan export teks satu baris yang ditinjau owner bila format
dokumen asli tidak didukung; jangan diam-diam menyederhanakan kondisi bisnis.

ID duplikat, hilang atau baru ditolak. Source harus merupakan salah satu requirement input workflow.
Pemeriksaan ini tidak dapat membuktikan bahwa report/manifest telah mencakup
seluruh requirement bisnis di luar scope yang dinyatakan.

## 2. Ambil binding untuk keputusan manusia

```bash
python3 -B /absolute/doforme/scripts/business_acceptance.py --repo /absolute/target --workflow /absolute/run --criteria /absolute/criteria.json
```

Tanpa --attestation, hasilnya selalu business_acceptance not_evaluated. Output
menyediakan binding_digest yang mencakup root repo, HEAD, manifest seluruh
working tree, config efektif, policy plugin, hasil workflow/bukti validasi, dan
manifest AC. Helper tidak menulis file. Jika ingin menyimpan keluaran, lakukan
secara eksplisit dari shell ke lokasi report yang sudah Anda pilih.

## 3. Owner menyiapkan artifact keputusan dan bukti UAT

Artifact berikut adalah format, bukan persetujuan yang dihasilkan AI. Isikan
identitas/role/provenance sebenarnya, timestamp dengan timezone, keputusan per
AC dan referensi bukti lokal yang sudah disediakan owner:

```json
{
  "contract_version": 1,
  "binding_digest": "COPY_EXACT_BINDING_DIGEST",
  "owner": {
    "name": "Identitas pemberi keputusan",
    "role": "Peran bisnis pemberi keputusan",
    "authority_reference": "Referensi mandat owner untuk scope ini"
  },
  "recorded_at": "2026-11-16T09:00:00+07:00",
  "decision_reference": "Referensi artifact keputusan yang benar-benar diberikan",
  "evidence_files": [
    {
      "id": "U1",
      "path": "/absolute/uat-notes.txt",
      "sha256": "COPY_ACTUAL_SHA256_OF_SUPPLIED_FILE"
    }
  ],
  "criteria": [
    {
      "id": "AC1",
      "decision": "accepted",
      "reason": "Penjelasan hasil inspeksi owner untuk kondisi AC1",
      "evidence_refs": ["U1"]
    }
  ]
}
```

accepted/rejected memerlukan sedikitnya satu referensi ke file bukti yang tidak
kosong dan hash-nya cocok. pending boleh tidak memiliki bukti. Seluruh AC tetap
harus memiliki keputusan eksplisit. URL saja tidak menggantikan konten UAT yang
dapat dibaca; file bukti dibatasi 5 MB, input JSON/source AC 1 MB, dan symlink/
special file ditolak. Isi/provenance bukti tetap merupakan supplied evidence,
bukan sesuatu yang otomatis terautentikasi karena hash cocok.

## 4. Validasi artifact tanpa mengubah workflow

```bash
python3 -B /absolute/doforme/scripts/business_acceptance.py --repo /absolute/target --workflow /absolute/run --criteria /absolute/criteria.json --attestation /absolute/owner-decision.json
```

| Hasil | Arti |
| --- | --- |
| not_evaluated | Tidak ada artifact manusia yang diberikan |
| attested_accepted | Artifact mengklaim accepted untuk seluruh AC pada binding ini |
| attested_rejected | Sedikitnya satu AC ditolak dalam artifact yang valid |
| attested_pending | Tidak ada penolakan, tetapi ada AC pending |
| Error/nonzero | Binding stale, integritas bermasalah, coverage salah, field tidak dikenal, provenance hilang atau bukti tidak cocok |

Exit 0 berarti struktur/binding artifact valid, **bukan** semua AC diterima:
rejected dan pending yang sah juga menghasilkan exit 0. Consumer harus membaca
business_acceptance serta decision_by_ac, bukan mengandalkan exit code saja.

owner_identity_verification dan owner_authority_verification tetap not_verified.
Utility ini tidak menyediakan login owner, tanda tangan digital, pemeriksaan
mandat organisasi, autentikasi Jira/Docs/Figma, atau penilaian semantik UAT.
Pihak yang menguasai repo dan artifact dapat merekayasa keduanya; hash hanya
mendeteksi perubahan terhadap binding yang dicatat, bukan pemalsuan oleh pihak
yang sama-sama mengubah semua sumber.

Output merupakan sidecar bukti terpisah. Skema summary runner lama tetap
business_acceptance not_evaluated; utility tidak menulis ulang history teknis.
resolution_status selalu not_established dan publication_ready selalu false.
Persetujuan publikasi, keputusan bahwa issue benar-benar resolved, dan tindakan
remote tetap membutuhkan kebijakan/otorisasi terpisah. Belum ada acceptance
bisnis nyata yang diklaim hanya karena fitur validator ini tersedia.

## Batas sebelum commit

Validator fase ini hanya berlaku selama HEAD **dan** konten tetap sama dengan
checkpoint yang diuji, termasuk pola baseline HEAD plus patch working tree.
Ambil binding dan validasi keputusan manusia sebelum membuat commit/push patch
tersebut. Bahkan commit yang byte-identik tetap mengubah HEAD dan membuat
acceptance validator menolak checkpoint sebagai stale. Ini batas yang disengaja;
jangan mengedit revision/report atau menghapus gate untuk menggunakan ulang
artifact lama.

Adapter publikasi memiliki handoff commit byte-identik yang terpisah, tetapi itu
hanya memverifikasi konten proposal PR. Handoff tersebut tidak memigrasikan atau
mengesahkan ulang acceptance manusia fase ini. Setelah commit, penggunaan ulang
acceptance memerlukan mekanisme validasi/keputusan baru yang belum didukung
validator ini; jangan mengklaim penerimaan bisnis baru berdasarkan draft PR.

## Pengujian

Tes memakai Git/checkpoint/artifact sintetis, bukan keputusan owner sungguhan.
Tes mencakup binding HEAD/content/report, asosiasi ID dengan entri source yang
sama (termasuk penolakan statement tertukar), layout ambigu/multiline, AC coverage, evidence hash, pemisahan
accepted/rejected/pending, penolakan field trust palsu dan inspeksi CLI tanpa
perubahan target/checkpoint. Tidak ada model call atau pesan ke owner dalam tes.
