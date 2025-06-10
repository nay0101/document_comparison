import re
import json
from helpers.document_processor import DocumentProcessor

document_processor = DocumentProcessor()

result = """
```json
{
  "total": 54,
  "flags": [
    {
      "location": "Document Title",
      "doc1": {
        "content": "<span style=\"color: red\">Emirates HLB World Elite</span>"
      },
      "doc2": {
        "content": ""
      },
      "discrepancies": [
        "1. The English version includes the title 'Emirates HLB World Elite' at the top, which is missing in the Bahasa Malaysia version."
      ],
      "explanation": "The English document has a brand/title line at the very top that is not present in the BM version."
    },
    {
      "location": "Section Title",
      "doc1": {
        "content": "HONG LEONG ESSENTIAL CREDIT CARD TERMS & CONDITIONS (Versi Bahasa Malaysia)"
      },
      "doc2": {
        "content": "TERMA & SYARAT KAD KREDIT HONG LEONG ESSENTIAL (English Version)"
      },
      "discrepancies": [
        "1. '(Versi Bahasa Malaysia)' in English version vs '(English Version)' in BM version.",
        "2. 'TERMA & SYARAT' is not a direct translation of 'TERMS & CONDITIONS' (missing 'CONDITIONS' translation)."
      ],
      "explanation": "The language version label is swapped, and the translation of 'TERMS & CONDITIONS' is not word-for-word."
    },
    {
      "location": "Last updated line",
      "doc1": {
        "content": "Last updated on 3 February 2025"
      },
      "doc2": {
        "content": "Dikemas Kini 3 Februari 2025"
      },
      "discrepancies": [
        "1. 'Last updated on' is not directly translated; 'Dikemas Kini' omits 'on'."
      ],
      "explanation": "The BM version omits the preposition 'on' from the date."
    },
    {
      "location": "Introductory Paragraph",
      "doc1": {
        "content": "These Hong Leong Essential Credit Card Terms and Conditions (' T&Cs ') are to be read together with the Hong Leong Bank Berhad's (' HLB ') Cardholder Agreement (' the Agreement '). Save and except for the variations set out below, all the terms and conditions of the Agreement shall apply. In the event of any discrepancy or inconsistency between the terms and conditions of the Agreement and these T&Cs, these T&Cs shall prevail in so far as they are applicable to the Hong Leong Essential Credit Card (' Essential Card '). By accepting the Essential Card, the Cardholder agrees to be bound by these T&Cs and the Agreement."
      },
      "doc2": {
        "content": "Terma dan syarat Kad Kredit Hong Leong Essential (' T&S' )  ini hendaklah dibaca bersama-sama dengan Perjanjian Pemegang Kad (' Perjanjian ') Hong Leong Bank Berhad (' HLB '). Selain daripada perubahan seperti tertera di bawah ini, semua terma dan syarat Perjanjian hendaklah diguna pakai. Sekiranya terdapat sebarang  percanggahan  antara  terma  dan  syarat  Perjanjian  dengan  T&S  ini,  maka  T&S  ini  hendaklah diutamakan setakat mana yang terpakai kepada Kad Kredit Hong Leong Essential ('Kad Essential') . Dengan menerima Kad Essential ini, Pemegang Kad bersetuju untuk terikat dengan T&S ini dan Perjanjian."
      },
      "discrepancies": [
        "1. 'Terms and Conditions' translated as 'Terma dan syarat' (missing 'dan' capitalization and ampersand).",
        "2. 'T&Cs' in English vs 'T&S' in BM (missing 'C' for 'Conditions' in BM abbreviation).",
        "3. 'Cardholder Agreement' translated as 'Perjanjian Pemegang Kad' (missing 'Cardholder' as a defined term).",
        "4. 'Save and except for the variations set out below' translated as 'Selain daripada perubahan seperti tertera di bawah ini' (missing 'save and except' direct translation).",
        "5. 'all the terms and conditions of the Agreement shall apply' translated as 'semua terma dan syarat Perjanjian hendaklah diguna pakai' (missing 'all the' direct translation).",
        "6. 'discrepancy or inconsistency' translated as 'percanggahan' (missing 'inconsistency' translation).",
        "7. 'these T&Cs shall prevail in so far as they are applicable' translated as 'T&S ini hendaklah diutamakan setakat mana yang terpakai' (missing 'in so far as' direct translation).",
        "8. 'By accepting the Essential Card, the Cardholder agrees to be bound by these T&Cs and the Agreement.' translated as 'Dengan menerima Kad Essential ini, Pemegang Kad bersetuju untuk terikat dengan T&S ini dan Perjanjian.' (missing 'by accepting' direct translation, and 'the Cardholder' not explicitly stated as a defined term)."
      ],
      "explanation": "Multiple word-level omissions and abbreviation inconsistencies between the two versions."
    },
    {
      "location": "Section 1. Definitions, (i)",
      "doc1": {
        "content": "' Card Account ' means the account of the Cardholder in respect of the Essential Card with the HLB."
      },
      "doc2": {
        "content": "'Akaun Kad' bermaksud akaun Pemegang Kad Utama yang dibuka bagi Kad dengan HLB."
      },
      "discrepancies": [
        "1. 'Cardholder' translated as 'Pemegang Kad Utama' (missing 'Supplementary Cardholder' inclusion).",
        "2. 'in respect of the Essential Card' translated as 'bagi Kad' (missing 'Essential' translation).",
        "3. 'with the HLB' translated as 'dengan HLB' (missing 'the' translation)."
      ],
      "explanation": "BM version restricts to 'Pemegang Kad Utama' (Principal Cardholder) and omits 'Essential' in 'Kad'."
    },
    {
      "location": "Section 1. Definitions, (ii)",
      "doc1": {
        "content": "' Cardholder ' means the individual named on the Essential Card whether ' Principal Cardholder ' and/or' Supplementary Cardholder ' unless stated otherwise."
      },
      "doc2": {
        "content": "'Pemegang Kad' bermaksud individu yang namanya tertera pada Kad sama ada ' Pemegang Kad Utama ' dan/atau ' Pemegang Kad Tambahan ' melainkan dinyatakan sebaliknya."
      },
      "discrepancies": [
        "1. 'Essential Card' translated as 'Kad' (missing 'Essential' translation).",
        "2. 'unless stated otherwise' translated as 'melainkan dinyatakan sebaliknya' (missing 'otherwise' direct translation)."
      ],
      "explanation": "BM omits 'Essential' in 'Kad' and does not translate 'otherwise' word-for-word."
    },
    {
      "location": "Section 1. Definitions, (iii)",
      "doc1": {
        "content": "' HLB Connect App ' means Hong Leong Bank Connect Mobile Banking Application"
      },
      "doc2": {
        "content": "'Pemegang Kad Tambahan' bermaksud individu yang kepadanya Kad Tambahan dikeluarkan oleh HLB berikutan permohanan oleh Pemegang Kad Utama."
      },
      "discrepancies": [
        "1. The English version defines 'HLB Connect App', but the BM version defines 'Pemegang Kad Tambahan' (Supplementary Cardholder) instead.",
        "2. The definition for 'HLB Connect App' is missing in this position in the BM version.",
        "3. The definition for 'Pemegang Kad Tambahan' is missing in the English version."
      ],
      "explanation": "The order and content of definitions are not aligned; each version contains a definition missing in the other."
    },
    {
      "location": "Section 1. Definitions, (iv)",
      "doc1": {
        "content": "' QR Pay Transaction' means retail transactions made via the HLB Connect App using the HLB QR Pay feature."
      },
      "doc2": {
        "content": "' HLB Connect App ' bermaksud Perbankan Mudah Alih Hong Leong Connect."
      },
      "discrepancies": [
        "1. The English version defines 'QR Pay Transaction', but the BM version defines 'HLB Connect App' instead.",
        "2. The definition for 'QR Pay Transaction' is missing in this position in the BM version.",
        "3. The definition for 'HLB Connect App' is missing in this position in the English version."
      ],
      "explanation": "Definitions are misaligned and not directly translated."
    },
    {
      "location": "Section 1. Definitions, (v)",
      "doc1": {
        "content": "' Statement ' means the periodic statement issued by the Bank to the Cardholder in relation to the Card  Account  which  shows  the  total  balance,  any  finance  charges,  fees,  charges,  minimum amount due and the payment due date."
      },
      "doc2": {
        "content": "'Transaksi QR Pay' transaksi runcit dibuat melalui HLB Connect App mengunakan QR Pay."
      },
      "discrepancies": [
        "1. The English version defines 'Statement', but the BM version defines 'Transaksi QR Pay' instead.",
        "2. The definition for 'Statement' is missing in this position in the BM version.",
        "3. The definition for 'Transaksi QR Pay' is missing in this position in the English version.",
        "4. 'mengunakan' is a spelling error; correct spelling is 'menggunakan'."
      ],
      "explanation": "Definitions are misaligned, and there is a spelling error in the BM version."
    },
    {
      "location": "Section 1. Definitions, (v) (BM)",
      "doc1": {
        "content": ""
      },
      "doc2": {
        "content": "' Penyata '  bermaksud  penyata  berkala  yang  dikeluarkan  oleh  HLB  kepada  Pemegang  Kad berhubung dengan Akaun Kad yang menunjukkan jumlah baki, sebarang caj kewangan, yuran, caj, jumlah minimum yang perlu dibayar dan tarikh akhir pembayaran."
      },
      "discrepancies": [
        "1. The BM version defines 'Penyata' (Statement) at (v), but the English version already used (v) for 'Statement' in the previous line, so the order is misaligned."
      ],
      "explanation": "Definition order is inconsistent between versions."
    },
    {
      "location": "Section 2. Cash Back, opening sentence",
      "doc1": {
        "content": "The Essential Card earns up to 1% Cashback on all Eligible Transactions (as defined below)."
      },
      "doc2": {
        "content": "Kad Essential memperoleh sehingga 1% Pulangan Tunai atas semua Transaksi yang sah (seperti ditakrif di bawah)."
      },
      "discrepancies": [
        "1. 'Eligible Transactions' translated as 'Transaksi yang sah' (should be 'Transaksi Yang Layak'; 'sah' means 'valid', not 'eligible')."
      ],
      "explanation": "BM uses 'sah' instead of 'layak', which is inconsistent with later usage and changes the meaning."
    },
    {
      "location": "Section 2. (i)",
      "doc1": {
        "content": "The earning of the respective Cashback is based on the respective Eligible Transactions stipulated in Table 1 below:"
      },
      "doc2": {
        "content": "Perolehan Pulangan Tunai masing-masing adalah berdasarkan Transaksi yang  layak yang dipaparkan dalam Jadual 1 di bawah:"
      },
      "discrepancies": [
        "1. 'Eligible Transactions' is not capitalized in BM ('Transaksi yang layak'), inconsistent with later usage.",
        "2. 'stipulated' translated as 'dipaparkan' (means 'displayed', not 'stipulated')."
      ],
      "explanation": "Capitalization and word choice discrepancies."
    },
    {
      "location": "Table 1, Header Row",
      "doc1": {
        "content": "| Eligible Transactions   | Eligible Merchant Category Codes (MCC), Merchants                                                                                       | Total Monthly Spend (Posted Eligible Transactions) & Cashback Entitlement   | Total Monthly Spend (Posted Eligible Transactions) & Cashback Entitlement   | Monthly Capping   |"
      },
      "doc2": {
        "content": "| Transaksi yang Layak    | Kad Kategori Peniaga (MCC), Peniaga dan/atau Transaksi Yang Layak                                                                 | Jumlah Perbelanjaan Bulanan (Transaksi Layak Diposkan) & Pulangan Tunai   | Jumlah Perbelanjaan Bulanan (Transaksi Layak Diposkan) & Pulangan Tunai   | Had Bulanan   |"
      },
      "discrepancies": [
        "1. 'Eligible Transactions' translated as 'Transaksi yang Layak' (should be capitalized consistently).",
        "2. 'Eligible Merchant Category Codes (MCC), Merchants' translated as 'Kad Kategori Peniaga (MCC), Peniaga dan/atau Transaksi Yang Layak' (adds 'Transaksi Yang Layak', which is not in English).",
        "3. 'Total Monthly Spend (Posted Eligible Transactions) & Cashback Entitlement' translated as 'Jumlah Perbelanjaan Bulanan (Transaksi Layak Diposkan) & Pulangan Tunai' (missing 'Entitlement' translation).",
        "4. 'Monthly Capping' translated as 'Had Bulanan' (missing 'Capping' nuance)."
      ],
      "explanation": "Header translations are not word-for-word and add or omit terms."
    },
    {
      "location": "Table 1, Second Header Row",
      "doc1": {
        "content": "| Eligible Transactions   | and/or Transactions                                                                                                                     | RM3,000 and below                                                           | Above RM3,000                                                               | Monthly Capping   |"
      },
      "doc2": {
        "content": "| Transaksi yang Layak    | Kad Kategori Peniaga (MCC), Peniaga dan/atau Transaksi Yang Layak                                                                 | RM3,000 dan ke bawah                                                      | RM3,000 ke atas                                                           | Had Bulanan   |"
      },
      "discrepancies": [
        "1. 'and/or Transactions' in English is replaced with 'Kad Kategori Peniaga (MCC), Peniaga dan/atau Transaksi Yang Layak' in BM (not a direct translation).",
        "2. 'RM3,000 and below' translated as 'RM3,000 dan ke bawah' (missing 'and' direct translation).",
        "3. 'Above RM3,000' translated as 'RM3,000 ke atas' (missing 'Above' direct translation)."
      ],
      "explanation": "BM version expands the second column and does not directly translate the English headers."
    },
    {
      "location": "Table 1, Insurance Row",
      "doc1": {
        "content": "| Insurance               | • MCC: 5960/6300                                                                                                                        | 0.50% cashback                                                              | 0.50% cashback                                                              | Unlimited         |"
      },
      "doc2": {
        "content": "| Insurans                | • MCC: 5960/6300                                                                                                                  | 0.50% pulangan tunai                                                      | 0.50% pulangan tunai                                                      | Tanpa Had     |"
      },
      "discrepancies": [
        "1. 'Insurance' translated as 'Insurans' (correct, but capitalization inconsistent).",
        "2. 'cashback' translated as 'pulangan tunai' (missing capitalization and not a direct translation).",
        "3. 'Unlimited' translated as 'Tanpa Had' (not a direct translation)."
      ],
      "explanation": "Minor capitalization and translation differences."
    },
    {
      "location": "Table 1, Retail Shopping Row",
      "doc1": {
        "content": "| Retail Shopping         | • MCC: 5309/5311/5611/5621/5 631/5641/5651/5655/56 61/5691/5699/5977 - Clothing and Accessories Stores, and/or Departmental Stores etc. | 0.50% cashback                                                              | 1.00% cashback                                                              | Unlimited         |"
      },
      "doc2": {
        "content": "| Perbelanjaan Runcit     | • MCC: 5309/5311/5611/562 1/5631/5641/5651/56 55/5661/5691/5699/5 977 - Kedai Pakaian dan Aksesori, dan/atau Gedung Serbaneka etc | 0.50% pulangan tunai                                                      | 1.00% pulangan tunai                                                      | Tanpa Had     |"
      },
      "discrepancies": [
        "1. 'Retail Shopping' translated as 'Perbelanjaan Runcit' (not a direct translation).",
        "2. MCC codes differ: English has '5621/5631/5655/5661/5977', BM has '562 1/5631/56 55/5661/5 977' (spacing and code order errors).",
        "3. 'Clothing and Accessories Stores, and/or Departmental Stores etc.' translated as 'Kedai Pakaian dan Aksesori, dan/atau Gedung Serbaneka etc' (missing 'Stores' translation and 'etc.' not localized)."
      ],
      "explanation": "MCC code formatting errors and incomplete translation of store types."
    },
    {
      "location": "Table 1, Travel Row",
      "doc1": {
        "content": "| Travel                  | • MCC: 3000 to 3299/3501 to 3999/4511/4722 to 4723/7011 - Airlines, Accommodations, Travel Agencies and Tour Operations etc.            | 0.50% cashback                                                              | 1.00% cashback                                                              | Unlimited         |"
      },
      "doc2": {
        "content": "| Perbelanjaan Perjalanan | • MCC: 3000 to 3299/3501 to 3999/4511/4722 to 4723/7011 - Penerbangan, Penginapan, Agensi Pelancongan dan Operasi Pelancongan     | 0.50% pulangan tunai                                                      | 1.00% pulangan tunai                                                      | Tanpa Had     |"
      },
      "discrepancies": [
        "1. 'Travel' translated as 'Perbelanjaan Perjalanan' (not a direct translation).",
        "2. 'Accommodations' translated as 'Penginapan' (missing plural form).",
        "3. 'Travel Agencies and Tour Operations etc.' translated as 'Agensi Pelancongan dan Operasi Pelancongan' (missing 'etc.' translation)."
      ],
      "explanation": "Translation is not word-for-word and omits 'etc.'"
    },
    {
      "location": "Table 1, Others Spend Row",
      "doc1": {
        "content": "| Others Spend            | • Any Other Eligible                                                                                                                    | 0.20% cashback                                                              | 0.20% cashback                                                              | Unlimited         |"
      },
      "doc2": {
        "content": "| Perbelanjaan            | • Semua Kod Kategori                                                                                                              | 0.20% pulangan tunai                                                      | 0.20% pulangan tunai                                                      | Tanpa Had     |"
      },
      "discrepancies": [
        "1. 'Others Spend' translated as 'Perbelanjaan' (missing 'Lain' or 'Lain-lain' for 'Others').",
        "2. 'Any Other Eligible' translated as 'Semua Kod Kategori' (missing 'Eligible' translation)."
      ],
      "explanation": "BM omits 'Others' and 'Eligible' in the translation."
    },
    {
      "location": "Table 1, Miscellaneous Row (BM only)",
      "doc1": {
        "content": ""
      },
      "doc2": {
        "content": "Lain\n\nPeniaga Peniaga Transaksi Layak\n\n(MCC), dan/atau Yang"
      },
      "discrepancies": [
        "1. The BM version has an extra line 'Lain Peniaga Peniaga Transaksi Layak (MCC), dan/atau Yang' which is not present in the English version."
      ],
      "explanation": "BM version contains an extra, possibly erroneous, line."
    },
    {
      "location": "Section 2. (ii)",
      "doc1": {
        "content": "' Eligible Transactions ' mean the retail transactions set out in Table 1 above which include  any purchase of any goods or services locally or overseas which have been effected with or charged to the Essential Card but shall EXCLUDE all Government, JomPAY and/or FPX transactions, Cash Advances, Quasi Cash (betting and gaming related transactions), Quick Cash (' QC '), Quick Cash One-Time  Fee  (' QC  OTF '),  Flexi  Payment  Plan  (' FPP '),  Balance  Transfers  (' BT '),  Finance Charges, Late Charges, Annual Fee Payment and QR Pay Transactions made via HLB Connect App. For the avoidance of doubt, the excluded list is not exhaustive and HLB reserves the sole right to determine if a transaction fall within the definition of  Eligible Transactions"
      },
      "doc2": {
        "content": "' Transaksi Yang Layak ' bermakna pembelian apa-apa barangan atau perkhidmatan di dalam atau luar negara yang telah dilakukan atau dicaj kepada Kad Essential tetapi TIDAK TERMASUK semua  transaksi  berkaitan  Kerajaan,  JomPAY  dan/atau  transaksi  FPX,  Pendahuluan  Tunai, Kuasi Tunai (transaksi berkaitan pertaruhan dan perjudian); Quick Cash (\" QC '), Pelan Bayaran Fleksi  (\" FPP '),  Pindahan  Baki  (' BT '),  Caj  Kewangan,  Caj  Lewat,  Bayaran  Fi  Tahunan  dan Transaksi QR Pay melalui HLB Connect App. Bagi mengelakkan keraguan, senarai di bawah ini tidak lengkap dan HLB berhak mutlak untuk menentukan bahawa sesuatu transaksi terangkum dalam takrif Transaksi Runcit."
      },
      "discrepancies": [
        "1. 'Eligible Transactions' translated as 'Transaksi Yang Layak' (inconsistent capitalization).",
        "2. 'retail transactions set out in Table 1 above which include any purchase of any goods or services locally or overseas' translated as 'pembelian apa-apa barangan atau perkhidmatan di dalam atau luar negara yang telah dilakukan atau dicaj kepada Kad Essential' (missing 'retail transactions set out in Table 1 above' direct translation).",
        "3. 'Essential Card' translated as 'Kad Essential' (missing 'the' translation).",
        "4. 'EXCLUDE all Government, JomPAY and/or FPX transactions, Cash Advances, Quasi Cash (betting and gaming related transactions), Quick Cash (' QC '), Quick Cash One-Time  Fee  (' QC  OTF '),  Flexi  Payment  Plan  (' FPP '),  Balance  Transfers  (' BT '),  Finance Charges, Late Charges, Annual Fee Payment and QR Pay Transactions made via HLB Connect App.' translated as 'TIDAK TERMASUK semua  transaksi  berkaitan  Kerajaan,  JomPAY  dan/atau  transaksi  FPX,  Pendahuluan  Tunai, Kuasi Tunai (transaksi berkaitan pertaruhan dan perjudian); Quick Cash (\" QC '), Pelan Bayaran Fleksi  (\" FPP '),  Pindahan  Baki  (' BT '),  Caj  Kewangan,  Caj  Lewat,  Bayaran  Fi  Tahunan  dan Transaksi QR Pay melalui HLB Connect App.' (missing 'Quick Cash One-Time Fee (QC OTF)' and 'Balance Transfers' is translated as 'Pindahan Baki' but omits 'Quick Cash One-Time Fee').",
        "5. 'For the avoidance of doubt, the excluded list is not exhaustive and HLB reserves the sole right to determine if a transaction fall within the definition of  Eligible Transactions' translated as 'Bagi mengelakkan keraguan, senarai di bawah ini tidak lengkap dan HLB berhak mutlak untuk menentukan bahawa sesuatu transaksi terangkum dalam takrif Transaksi Runcit.' (missing 'Eligible Transactions' translation, uses 'Transaksi Runcit' instead)."
      ],
      "explanation": "BM omits 'Quick Cash One-Time Fee', uses 'Transaksi Runcit' instead of 'Transaksi Yang Layak', and does not translate some qualifiers."
    },
    {
      "location": "Section 2. (iii)",
      "doc1": {
        "content": "The Cashback shall be credited to and be reflected in the Cardholder's monthly Statement on each billing cycle/statement date."
      },
      "doc2": {
        "content": "Pulangan Tunai akan dikreditkan dan dipaparkan dalam Penyata bulanan Pemegang Kad pada setiap kitaran bil/tarikh penyata."
      },
      "discrepancies": [
        "1. 'The Cashback shall be credited to and be reflected in' translated as 'Pulangan Tunai akan dikreditkan dan dipaparkan dalam' (missing 'shall be' direct translation).",
        "2. 'Cardholder's monthly Statement' translated as 'Penyata bulanan Pemegang Kad' (missing possessive form)."
      ],
      "explanation": "BM omits possessive and modal verb."
    },
    {
      "location": "Section 2. (iv)",
      "doc1": {
        "content": "The  Cashback  will  be  calculated  at  the  end  of  each  billing  cycle/statement.  The  cumulated Cashback shall be posted to the Cardholder's monthly Statement. The Cashback credits may or will be utilized towards any outstanding balance due on the Card Account. For the avoidance of doubt, any Cashback due to the Cardholder will be posted in the Card Account and reflected in the Cardholder's Statement for the particular month. In the event the Cashback due to the Cardholder is on the date of the Cardholder's Statement, the Cashback will only be reflected in the Cardholder's Statement in the following month. In the event the Cardholder's Statement is on day thirty-one (31) of the month, the Cashback will only be reflected in the Cardholder's Statement once every two (2) months."
      },
      "doc2": {
        "content": "Pulangan Tunai akan dikira pada akhir setiap kitaran bil/tarikh penyata. Pulangan Tunai terkumpul akan dikreditkan kepada Penyata bulanan Pemegang Kad. Kredit Pulangan Tunai boleh atau akan digunakan untuk menjelaskan apa-apa baki belum lunas yang tertunggak dalam Akaun Kad. Bagi mengelakkan keraguan, apa-apa Pulangan Tunai yang perlu dibayar kepada Pemegang Kad akan dicatatkan dalam Akaun Kad dan dipaparkan dalam Penyata Pemegang Kad bagi bulan berkenaan. Sekiranya Pulangan Tunai yang perlu dibayar kepada Pemegang Kad adalah pada tarikh Penyata Pemegang Kad, maka Pulangan Tunai hanya akan dipaparkan dalam Penyata Pemegang Kad pada bulan berikutnya. Sekiranya Penyata Pemegang Kad adalah pada hari ketiga puluh satu (31) bulan itu, Pulangan Tunai hanya akan dipaparkan dalam Penyata Pemegang Kad setiap dua   (2) bulan sekali."
      },
      "discrepancies": [
        "1. 'The Cashback credits may or will be utilized towards any outstanding balance due on the Card Account.' translated as 'Kredit Pulangan Tunai boleh atau akan digunakan untuk menjelaskan apa-apa baki belum lunas yang tertunggak dalam Akaun Kad.' (missing 'may or will be utilized towards' direct translation).",
        "2. 'For the avoidance of doubt, any Cashback due to the Cardholder will be posted in the Card Account and reflected in the Cardholder's Statement for the particular month.' translated as 'Bagi mengelakkan keraguan, apa-apa Pulangan Tunai yang perlu dibayar kepada Pemegang Kad akan dicatatkan dalam Akaun Kad dan dipaparkan dalam Penyata Pemegang Kad bagi bulan berkenaan.' (missing 'for the particular month' direct translation).",
        "3. 'In the event the Cashback due to the Cardholder is on the date of the Cardholder's Statement, the Cashback will only be reflected in the Cardholder's Statement in the following month.' translated as 'Sekiranya Pulangan Tunai yang perlu dibayar kepada Pemegang Kad adalah pada tarikh Penyata Pemegang Kad, maka Pulangan Tunai hanya akan dipaparkan dalam Penyata Pemegang Kad pada bulan berikutnya.' (missing 'due to the Cardholder' direct translation).",
        "4. 'In the event the Cardholder's Statement is on day thirty-one (31) of the month, the Cashback will only be reflected in the Cardholder's Statement once every two (2) months.' translated as 'Sekiranya Penyata Pemegang Kad adalah pada hari ketiga puluh satu (31) bulan itu, Pulangan Tunai hanya akan dipaparkan dalam Penyata Pemegang Kad setiap dua   (2) bulan sekali.' (missing 'once every' direct translation)."
      ],
      "explanation": "BM omits some qualifiers and direct translations."
    },
    {
      "location": "Section 2. (v)",
      "doc1": {
        "content": "HLB reserves its rights from time to time, with prior notice, to revise the Cashback percentage at its discretion."
      },
      "doc2": {
        "content": "HLB berhak dari semasa ke semasa, setelah memberi notis awal, meminda peratusan Pulangan Tunai menurut budi bicaranya."
      },
      "discrepancies": [
        "1. 'reserves its rights from time to time, with prior notice, to revise' translated as 'berhak dari semasa ke semasa, setelah memberi notis awal, meminda' (missing 'reserves its rights' direct translation).",
        "2. 'at its discretion' translated as 'menurut budi bicaranya' (not a direct translation)."
      ],
      "explanation": "BM omits 'reserves its rights' and uses a different phrase for 'at its discretion'."
    },
    {
      "location": "Section 2. (vi)",
      "doc1": {
        "content": "An illustration  of  the  Cashback  for  monthly  spend  above  RM3,000    on  Eligible  Transactions  is provided below in Table 2:"
      },
      "doc2": {
        "content": "Ilustrasi Pulangan Tunai untuk perbelanjaan bulanan melebihi RM3,000 untuk Transaksi Layak disediakan di bawah dalam Jadual 2:"
      },
      "discrepancies": [
        "1. 'Eligible Transactions' translated as 'Transaksi Layak' (missing 'Yang' for capitalization consistency).",
        "2. 'is provided below in Table 2' translated as 'disediakan di bawah dalam Jadual 2' (missing 'provided' direct translation)."
      ],
      "explanation": "Minor translation and capitalization inconsistencies."
    },
    {
      "location": "Table 2, Retail Shopping Row",
      "doc1": {
        "content": "| Retail Shopping                              | 600           | 600 x 1% = RM6              |                   6   |"
      },
      "doc2": {
        "content": "| Perbelanjaan Runcit                                          | 600           | 600 x 1% = RM6                  |                          6   |"
      },
      "discrepancies": [
        "1. 'Retail Shopping' translated as 'Perbelanjaan Runcit' (not a direct translation)."
      ],
      "explanation": "Translation is not word-for-word."
    },
    {
      "location": "Table 2, Travel Row",
      "doc1": {
        "content": "| Travel (eg: Agoda & etc)                     | 1,000         | 1,000 x 1% = RM10           |                  10   |"
      },
      "doc2": {
        "content": "| Perbelanjaan Perjalanan (eg: Agoda etc)                      | 1,000         | 1,000 x 1% = RM10               |                         10   |"
      },
      "discrepancies": [
        "1. 'Travel (eg: Agoda & etc)' translated as 'Perbelanjaan Perjalanan (eg: Agoda etc)' (missing '&' and 'etc.' not localized)."
      ],
      "explanation": "BM omits '&' and does not localize 'etc.'"
    },
    {
      "location": "Table 2, Others Spend Row",
      "doc1": {
        "content": "| Others Spend (Dining, Groceries, Petrol etc) | 600           | 600 x 0.2% = RM1.20         |                   1.2 |"
      },
      "doc2": {
        "content": "| Perbelanjaan Lain (Jamu Selera, Barangan Runcit, Petrol etc) | 600           | 600 x 0.2% = RM1.20             |                          1.2 |"
      },
      "discrepancies": [
        "1. 'Others Spend (Dining, Groceries, Petrol etc)' translated as 'Perbelanjaan Lain (Jamu Selera, Barangan Runcit, Petrol etc)' (missing 'Groceries' direct translation, 'Dining' translated as 'Jamu Selera')."
      ],
      "explanation": "BM uses 'Jamu Selera' for 'Dining' and omits 'Groceries'."
    },
    {
      "location": "Table 2, Monthly Eligible Spend Row",
      "doc1": {
        "content": "| Monthly Eligible Spend                       | 3,200         |                             |                  22.2 |"
      },
      "doc2": {
        "content": "| Perbelanjaan Layak Bulanan                                   | 3,200         |                                 |                         22.2 |"
      },
      "discrepancies": [
        "1. 'Monthly Eligible Spend' translated as 'Perbelanjaan Layak Bulanan' (word order reversed)."
      ],
      "explanation": "BM reverses the word order."
    },
    {
      "location": "Section 2. (vi), after Table 2",
      "doc1": {
        "content": "For clarity, JomPay is not eligible for the Cashback as stipulated under Clause 2(ii) above."
      },
      "doc2": {
        "content": "Untuk kejelasan, transaksi JomPay tidak layak untuk Pulangan Tunai seperti yang ditetapkan di bawah Klausa 2(ii) di atas."
      },
      "discrepancies": [
        "1. 'For clarity' translated as 'Untuk kejelasan' (missing 'clarity' direct translation).",
        "2. 'JomPay is not eligible for the Cashback' translated as 'transaksi JomPay tidak layak untuk Pulangan Tunai' (missing 'the' and 'the Cashback' direct translation)."
      ],
      "explanation": "BM omits some direct translations."
    },
    {
      "location": "Section 2. (vii)",
      "doc1": {
        "content": "An illustration  of  the  Cashback  for  monthly  spend  below  RM3,000    on  Eligible  Transactions  is provided below in Table 3:"
      },
      "doc2": {
        "content": "Ilustrasi  Pulangan  Tunai  untuk  perbelanjaan  bulanan  di  bawah  RM3,000  untuk  Transaksi Layak disediakan di bawah dalam Jadual 3:"
      },
      "discrepancies": [
        "1. 'Eligible Transactions' translated as 'Transaksi Layak' (missing 'Yang' for capitalization consistency).",
        "2. 'is provided below in Table 3' translated as 'disediakan di bawah dalam Jadual 3' (missing 'provided' direct translation)."
      ],
      "explanation": "Minor translation and capitalization inconsistencies."
    },
    {
      "location": "Table 3, Retail Shopping Row",
      "doc1": {
        "content": "| Retail Shopping                              | 500           | 500 x 0.5% = RM2.50         |                   2.5 |"
      },
      "doc2": {
        "content": "| Perbelanjaan Runcit                                          | 500           | 500 x 0.5% = RM2.50             |                          2.5 |"
      },
      "discrepancies": [
        "1. 'Retail Shopping' translated as 'Perbelanjaan Runcit' (not a direct translation)."
      ],
      "explanation": "Translation is not word-for-word."
    },
    {
      "location": "Table 3, Travel Row",
      "doc1": {
        "content": "| Travel (eg: Agoda & etc)                     | 600           | 600 x 0.5% = RM3            |                   3   |"
      },
      "doc2": {
        "content": "| Perbelanjaan Perjalanan (eg: Agoda etc)                      | 600           | 600 x 0.5% = RM3                |                          3   |"
      },
      "discrepancies": [
        "1. 'Travel (eg: Agoda & etc)' translated as 'Perbelanjaan Perjalanan (eg: Agoda etc)' (missing '&' and 'etc.' not localized)."
      ],
      "explanation": "BM omits '&' and does not localize 'etc.'"
    },
    {
      "location": "Table 3, Others Spend Row",
      "doc1": {
        "content": "| Others Spend (Dining, Groceries, Petrol etc) | 600           | 600 x 0.2% = RM1.20         |                   1.2 |"
      },
      "doc2": {
        "content": "| Perbelanjaan Lain (Jamu Selera, Barangan Runcit, Petrol etc) | 600           | 600 x 0.2% = RM1.20             |                          1.2 |"
      },
      "discrepancies": [
        "1. 'Others Spend (Dining, Groceries, Petrol etc)' translated as 'Perbelanjaan Lain (Jamu Selera, Barangan Runcit, Petrol etc)' (missing 'Groceries' direct translation, 'Dining' translated as 'Jamu Selera')."
      ],
      "explanation": "BM uses 'Jamu Selera' for 'Dining' and omits 'Groceries'."
    },
    {
      "location": "Table 3, Monthly Eligible Spend Row",
      "doc1": {
        "content": "| Monthly Eligible Spend                       | 2,200         |                             |                   9.2 |"
      },
      "doc2": {
        "content": "| Perbelanjaan Layak Bulanan                                   | 2,200         |                                 |                          9.2 |"
      },
      "discrepancies": [
        "1. 'Monthly Eligible Spend' translated as 'Perbelanjaan Layak Bulanan' (word order reversed)."
      ],
      "explanation": "BM reverses the word order."
    },
    {
      "location": "Section 2. (vii), after Table 3",
      "doc1": {
        "content": "For clarity, JomPay is not eligible for the Cashback as stipulated under Clause 2(ii) above."
      },
      "doc2": {
        "content": "Untuk kejelasan, transaksi JomPay tidak layak untuk Pulangan Tunai seperti yang ditetapkan di bawah Klausa 2(ii) di atas."
      },
      "discrepancies": [
        "1. 'For clarity' translated as 'Untuk kejelasan' (missing 'clarity' direct translation).",
        "2. 'JomPay is not eligible for the Cashback' translated as 'transaksi JomPay tidak layak untuk Pulangan Tunai' (missing 'the' and 'the Cashback' direct translation)."
      ],
      "explanation": "BM omits some direct translations."
    },
    {
      "location": "Section 3. Product Features Variation",
      "doc1": {
        "content": "HLB shall be entitled to, and from time to time, amend, vary or alter any of the product features for the Essential Card or withdraw the Essential Card at any time, with prior notice to the Cardholder and such amendments shall be effective on such date that HLB may elect to adopt. Subsequently, HLB may mail directly to the Cardholder or notify in the mass media or posting up a notice in HLB's banking hall or HLB's website at www.hlb.com.my or any method which HLB deems practical for such additions, modifications or amendments of the product features."
      },
      "doc2": {
        "content": "HLB berhak, dan dari semasa ke semasa, meminda, mengubah atau menukar mana-mana ciri-ciri produk bagi Kad Essential atau menarik balik Kad Essential pada bila-bila masa, telah memberi notis awal kepada Pemegang Kad dan pindaan tersebut adalah berkuat kuasa pada tarikh yang HLB pilih untuk dilaksanakan. Seiring itu, HLB boleh terus menghantar kepada Pemegang Kad atau membuat pemakluman dalam media massa atau meletak notis dalam dewan legar HLB atau laman web HLB di www.hlb.com.my atau apa-apa cara yang HLB dapati sesuai berkenaan penambahan, pengubahsuaian atau pemindaan tersebut tentang ciri-ciri produk berkenaan."
      },
      "discrepancies": [
        "1. 'shall be entitled to, and from time to time, amend, vary or alter' translated as 'berhak, dan dari semasa ke semasa, meminda, mengubah atau menukar' (missing 'shall be entitled to' direct translation).",
        "2. 'withdraw the Essential Card at any time, with prior notice to the Cardholder' translated as 'menarik balik Kad Essential pada bila-bila masa, telah memberi notis awal kepada Pemegang Kad' (should be 'setelah memberi notis awal', not 'telah').",
        "3. 'such amendments shall be effective on such date that HLB may elect to adopt' translated as 'pindaan tersebut adalah berkuat kuasa pada tarikh yang HLB pilih untuk dilaksanakan' (missing 'may elect to adopt' direct translation).",
        "4. 'HLB may mail directly to the Cardholder or notify in the mass media or posting up a notice in HLB's banking hall or HLB's website at www.hlb.com.my or any method which HLB deems practical' translated as 'HLB boleh terus menghantar kepada Pemegang Kad atau membuat pemakluman dalam media massa atau meletak notis dalam dewan legar HLB atau laman web HLB di www.hlb.com.my atau apa-apa cara yang HLB dapati sesuai' (missing 'directly' and 'posting up a notice' direct translation).",
        "5. 'for such additions, modifications or amendments of the product features' translated as 'berkenaan penambahan, pengubahsuaian atau pemindaan tersebut tentang ciri-ciri produk berkenaan' (word order and direct translation missing)."
      ],
      "explanation": "BM omits some direct translations and uses different word order."
    },
    {
      "location": "Section 4. Interpretation, (a)",
      "doc1": {
        "content": "Unless the context otherwise requires, capitalized words and expressions shall have the same meaning as defined in the Agreement unless specifically defined in these T&Cs."
      },
      "doc2": {
        "content": "Melainkan  konteks  menghendaki  sebaliknya,  perkataan  dan  ungkapan  yang  berhuruf  besar mempunyai pengertian yang sama seperti mana ditakrif dalam Perjanjian kecuali ditakrif secara khusus dalam T&S ini."
      },
      "discrepancies": [
        "1. 'capitalized words and expressions' translated as 'perkataan dan ungkapan yang berhuruf besar' (missing 'expressions' direct translation).",
        "2. 'shall have the same meaning as defined in the Agreement unless specifically defined in these T&Cs' translated as 'mempunyai pengertian yang sama seperti mana ditakrif dalam Perjanjian kecuali ditakrif secara khusus dalam T&S ini' (missing 'shall have' direct translation)."
      ],
      "explanation": "BM omits some direct translations."
    },
    {
      "location": "Section 4. Interpretation, (b)",
      "doc1": {
        "content": "Words referring to the male gender shall include the female and/or neuter gender and vice versa."
      },
      "doc2": {
        "content": "Perkataan yang merujuk jantina lelaki akan termasuk jantina perempuan dan/atau jantina neutral, dan begitu juga sebaliknya."
      },
      "discrepancies": [
        "1. 'Words referring to the male gender' translated as 'Perkataan yang merujuk jantina lelaki' (missing 'referring to' direct translation).",
        "2. 'shall include the female and/or neuter gender and vice versa' translated as 'akan termasuk jantina perempuan dan/atau jantina neutral, dan begitu juga sebaliknya' (missing 'shall include' direct translation)."
      ],
      "explanation": "BM omits some direct translations."
    },
    {
      "location": "Section 4. Interpretation, (c)",
      "doc1": {
        "content": "Words referring to the singular number shall include plural number and vice versa."
      },
      "doc2": {
        "content": "Perkataan  yang  merujuk  bilangan  tunggal  akan  termasuk  bilangan  jamak,  dan  begitu  juga sebaliknya."
      },
      "discrepancies": [
        "1. 'Words referring to the singular number' translated as 'Perkataan  yang  merujuk  bilangan  tunggal' (missing 'referring to' direct translation).",
        "2. 'shall include plural number and vice versa' translated as 'akan  termasuk  bilangan  jamak,  dan  begitu  juga sebaliknya' (missing 'shall include' direct translation)."
      ],
      "explanation": "BM omits some direct translations."
    },
    {
      "location": "Contact/Enquiries Paragraph",
      "doc1": {
        "content": "If you have any enquiries regarding these T&Cs, you may seek clarification from our staff who attended to you. Alternatively, please email us at hlonline@hlbb.hongleong.com.my."
      },
      "doc2": {
        "content": "Jika  anda  mempunyai  sebarang  pertanyaan  mengenai  T&S  ini,  anda  boleh  mendapatkan  penjelasan daripada  kakitangan  kami  yang  sedang  melayani  anda.  Sebagai  alternatif,  sila  e-mel  kepada  kami  di hlonline@hlbb.hongleong.com.my."
      },
      "discrepancies": [
        "1. 'enquiries' translated as 'pertanyaan' (could also be 'soalan' for 'questions').",
        "2. 'seek clarification from our staff who attended to you' translated as 'mendapatkan penjelasan daripada kakitangan kami yang sedang melayani anda' (missing 'who attended to you' direct translation).",
        "3. 'please email us at' translated as 'sila e-mel kepada kami di' (missing 'please' direct translation)."
      ],
      "explanation": "BM omits some direct translations."
    },
    {
      "location": "General: Use of English in BM version",
      "doc1": {
        "content": ""
      },
      "doc2": {
        "content": "eg: Agoda etc"
      },
      "discrepancies": [
        "1. The BM version uses 'eg:' and 'etc' in English, which should be localized to 'cth:' and 'dan lain-lain'."
      ],
      "explanation": "BM version contains English abbreviations."
    },
    {
      "location": "General: Spelling error in BM version",
      "doc1": {
        "content": ""
      },
      "doc2": {
        "content": "mengunakan"
      },
      "discrepancies": [
        "1. 'mengunakan' is a spelling error; correct spelling is 'menggunakan'."
      ],
      "explanation": "Spelling error in BM version."
    },
    {
      "location": "General: Inconsistent abbreviation for T&Cs",
      "doc1": {
        "content": "T&Cs"
      },
      "doc2": {
        "content": "T&S"
      },
      "discrepancies": [
        "1. 'T&Cs' in English vs 'T&S' in BM (missing 'C' for 'Conditions' in BM abbreviation)."
      ],
      "explanation": "Abbreviation is inconsistent between versions."
    }
  ]
}
```
"""
json_str = result
final = document_processor.extract_json_from_markdown(json_str)
# result_dict = json.loads(final)
# print(result_dict.get("flags"))
print(final)
