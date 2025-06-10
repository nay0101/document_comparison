import re
import json
from helpers.document_processor import DocumentProcessor

document_processor = DocumentProcessor()

result = """```json
```json
{
  "total": "74",
  "flags": [
    {
      "location": "Opening Title",
      "doc1": {
        "content": "HONG LEONG DEBIT CARD TERMS AND CONDITIONS (Versi Bahasa Malaysia)"
      },
      "doc2": {
        "content": "TERMA DAN SYARAT KAD DEBIT HONG LEONG (English Version)"
      },
      "discrepancies": [
        "1. '(Versi Bahasa Malaysia)' in English version vs '(English Version)' in BM version.",
        "2. The English version is titled in English, BM version is titled in BM.",
        "3. The English version includes 'Last updated on 6 January 2025', BM version uses 'Dikemaskini pada 6 Januari 2025'."
      ],
      "explanation": "The language of the version label is swapped, and the update date phrase is translated differently."
    },
    {
      "location": "Opening Paragraph",
      "doc1": {
        "content": "In consideration of Hong Leong Bank Berhad or Hong Leong Islamic Bank Berhad (' the Bank ') agreeing to provide the Cardholder with the Services (as defined under Clause 1.58) and agreeing to issue the Debit Card (as  defined  under  Clause  1)  including  Affinity  (as  defined  under  Clause  1.2)  to  the  Cardholder  at  the Cardholder's request, the Cardholder covenants and agrees that the Cardholder's signing on the Debit Card, use  of  the  Debit  Card  and/or  maintaining  an  Account  (as  defined  under  Clause  1)  shall  constitute  the Cardholder's agreement to the terms and conditions (' T&amp;Cs ') below."
      },
      "doc2": {
        "content": "Sebagai pertimbangan Hong Leong Bank Berhad atau Hong Leong Islamic Bank Berhad (\" Bank \")bersetuju untuk menyediakan Perkhidmatan dan bersetuju untuk mengeluarkan Kad Debit (seperti yang ditentukan dalam Klausa 1) termasuk Gabungan (sebagaimana didefinisikan dalam Klausa 1.2) kepada Pemegang Kad  atas  permohonan  Pemegang  Kad,  Pemegang  Kad  berjanji  dan  bersetuju  bahawa  penurunan tandatangan pada Kad Debit, penggunaan Kad Debit dan/atau pengekalan Akaun oleh Pemegang Kad akan membentuk perjanjian Pemegang Kad dengan terma dan syarat (' T&amp;S ') di bawah."
      },
      "discrepancies": [
        "1. 'the Services (as defined under Clause 1.58)' is omitted in BM version.",
        "2. 'as defined under Clause 1' for Debit Card is translated as 'seperti yang ditentukan dalam Klausa 1' (acceptable).",
        "3. 'including Affinity (as defined under Clause 1.2)' is translated as 'termasuk Gabungan (sebagaimana didefinisikan dalam Klausa 1.2)' (acceptable).",
        "4. 'at the Cardholder's request' is translated as 'atas permohonan Pemegang Kad' (acceptable).",
        "5. 'the Cardholder covenants and agrees' is translated as 'Pemegang Kad berjanji dan bersetuju' (acceptable).",
        "6. 'the Cardholder's signing on the Debit Card, use of the Debit Card and/or maintaining an Account (as defined under Clause 1)' is translated as 'penurunan tandatangan pada Kad Debit, penggunaan Kad Debit dan/atau pengekalan Akaun oleh Pemegang Kad' (acceptable).",
        "7. 'shall constitute the Cardholder's agreement to the terms and conditions (' T&amp;Cs ') below.' is translated as 'akan membentuk perjanjian Pemegang Kad dengan terma dan syarat (' T&S ') di bawah.' (acceptable).",
        "8. The phrase 'as defined under Clause 1' after 'Account' is omitted in BM version."
      ],
      "explanation": "BM version omits the explicit reference to 'the Services (as defined under Clause 1.58)' and the definition reference after 'Account'."
    },
    {
      "location": "Opening Paragraph, Second Sentence",
      "doc1": {
        "content": "These T&amp;Cs are to be read together as a whole with the Bank's General Terms and Conditions of Accounts, Terms and Conditions for the Use of HLB Connect and any other relevant Account terms and conditions, as well as other rules and regulations binding on the Bank. The following definitions apply unless otherwise stated:"
      },
      "doc2": {
        "content": "T&amp;S ini  hendaklah  dibaca  bersama  sebagai  keseluruhan  dengan  Terma  dan  Syarat  Am  Akaun  Bank, Terma dan Syarat Penggunaan HLB Connect dan sebarang terma dan syarat akaun yang berkaitan, serta syarat dan peraturan lain yang mengikat Bank. Definisi berikut berkuatkuasa kecuali dinyatakan sebaliknya:"
      },
      "discrepancies": [
        "1. 'as a whole' is omitted in BM version.",
        "2. 'other rules and regulations binding on the Bank' is translated as 'syarat dan peraturan lain yang mengikat Bank' (acceptable).",
        "3. 'The following definitions apply unless otherwise stated:' is translated as 'Definisi berikut berkuatkuasa kecuali dinyatakan sebaliknya:' (acceptable)."
      ],
      "explanation": "BM version omits 'as a whole'."
    },
    {
      "location": "Definition 1.1",
      "doc1": {
        "content": "' Account ' means the Cardholder's account or accounts with HLB/HLISB and shall include any other new accounts which may be opened from time to time."
      },
      "doc2": {
        "content": "'Akaun' bermaksud akaun atau akaun-akaun Pelanggan dengan HLB / HLISB dan hendaklah termasuk mana-mana akaun baharu lain yang dibuka dari semasa ke semasa"
      },
      "discrepancies": [
        "1. 'Cardholder's account or accounts' is translated as 'akaun atau akaun-akaun Pelanggan', but 'Pelanggan' is not defined as 'Pemegang Kad' (potential terminology inconsistency).",
        "2. 'which may be opened from time to time' is translated as 'yang dibuka dari semasa ke semasa', omitting 'may be'."
      ],
      "explanation": "BM version uses 'Pelanggan' instead of 'Pemegang Kad', and omits 'may be' in the phrase about new accounts."
    },
    {
      "location": "Definition 1.5",
      "doc1": {
        "content": "' ATM ' means the automated teller machines: (a) installed by the Bank or any member of the Shared ATM Network (SAN); and/or (b) designated by the Bank or Visa/Mastercard, for the use of the Cardholder."
      },
      "doc2": {
        "content": "'ATM' bermaksud mesin juruwang automatik: (a) yang dipasang oleh Bank atau mana-mana ahli Rangkaian ATM Kongsi (Shared ATM Network (SAN)); dan/atau (b) ditetapkan oleh Bank atau Visa/Mastercard, untuk penggunaan Pemegang Kad."
      },
      "discrepancies": [
        "1. 'for the use of the Cardholder' is translated as 'untuk penggunaan Pemegang Kad' (acceptable).",
        "2. 'automated teller machines' is translated as 'mesin juruwang automatik' (acceptable).",
        "3. 'installed by the Bank or any member of the Shared ATM Network (SAN)' is translated as 'yang dipasang oleh Bank atau mana-mana ahli Rangkaian ATM Kongsi (Shared ATM Network (SAN))' (acceptable).",
        "4. 'designated by the Bank or Visa/Mastercard' is translated as 'ditetapkan oleh Bank atau Visa/Mastercard' (acceptable)."
      ],
      "explanation": "No significant discrepancies; translation is accurate."
    },
    {
      "location": "Definition 1.7",
      "doc1": {
        "content": "' Authorised Cash Outlets ' means branch, office and/or location designated by members of Shared ATM Network, Visa/Mastercard to affect cash withdrawal."
      },
      "doc2": {
        "content": "'Rangkaian Tunai Dibenarkan' bermaksud cawangan, pejabat dan/atau lokasi yang ditetapkan oleh Rangkaian ATM Kongsi, Visa/Mastercard untuk melaksanakan pengeluaran wang tunai."
      },
      "discrepancies": [
        "1. 'designated by members of Shared ATM Network, Visa/Mastercard' is translated as 'ditetapkan oleh Rangkaian ATM Kongsi, Visa/Mastercard', omitting 'members of'.",
        "2. 'to affect cash withdrawal' is translated as 'untuk melaksanakan pengeluaran wang tunai' (acceptable)."
      ],
      "explanation": "BM version omits 'members of' before 'Rangkaian ATM Kongsi'."
    },
    {
      "location": "Definition 1.8",
      "doc1": {
        "content": "' Authorised Merchant ' means any retailer or corporation which pursuant to a Merchant Agreement agrees to accept or cause its outlets to accept the Debit Card for payment or pursuant to a legal arrangement with MyDebit/Visa/Mastercard agree to accept or cause its outlets to accept the facilities offered by co-branded Visa/Mastercard for payment."
      },
      "doc2": {
        "content": "'Peniaga  Sah' bermaksud mana-mana peruncit atau perbadanan yang mana selaras dengan Perjanjian Peniaga bersetuju untuk menerima atau menyebabkan outletnya menerima Kad Debit untuk pembayaran atau menurut kepada perkiraan undang-undang dengan MyDebit/Visa/Mastercard  bersetuju  untuk  menerima  atau  menyebabkan  rangkaiannya  untuk menerima kemudahan yang ditawarkan bergabung atau berkongsi jenama Visa/Mastercard untuk pembayaran."
      },
      "discrepancies": [
        "1. 'cause its outlets to accept' is translated as 'menyebabkan outletnya menerima' (acceptable).",
        "2. 'facilities offered by co-branded Visa/Mastercard' is translated as 'kemudahan yang ditawarkan bergabung atau berkongsi jenama Visa/Mastercard', which adds 'berkongsi jenama' (co-branding) but omits 'facilities' as a plural concept.",
        "3. 'legal arrangement' is translated as 'perkiraan undang-undang' (acceptable)."
      ],
      "explanation": "BM version adds 'berkongsi jenama' (shared brand) which is not in English, and omits pluralization of 'facilities'."
    },
    {
      "location": "Definition 1.10",
      "doc1": {
        "content": "' Bank ' means either Hong Leong Bank Berhad (193401000023 (97141-X)) or Hong Leong Islamic Bank Berhad (200501009144 (686191-W)) and includes its successors-in-title and assigns."
      },
      "doc2": {
        "content": "'Bank' bermaksud sama ada Hong Leong Bank Berhad (193401000023 (97141-X)) atau Hong Leong Islamic Bank Berhad (200501009144 (686191-W)) dan termasuk pewaris-namanya dan pemegang serah-hak dibenarkan."
      },
      "discrepancies": [
        "1. 'successors-in-title and assigns' is translated as 'pewaris-namanya dan pemegang serah-hak dibenarkan', which omits 'assigns' as a separate concept.",
        "2. 'pewaris-namanya' is not a standard legal term for 'successors-in-title'."
      ],
      "explanation": "BM version uses non-standard legal terms for 'successors-in-title and assigns'."
    },
    {
      "location": "Definition 1.13",
      "doc1": {
        "content": "' Card Replacement Fee '  means  fees  imposed  on  the  Cardholder  in  the  event  of  loss,  stolen  or damaged card."
      },
      "doc2": {
        "content": "'Fi Penggantian Kad' bermaksud fi yang dikenakan ke atas Pemegang Kad jika kad hilang, dicuri atau rosak."
      },
      "discrepancies": [
        "1. 'in the event of loss, stolen or damaged card' is translated as 'jika kad hilang, dicuri atau rosak' (acceptable)."
      ],
      "explanation": "No significant discrepancies."
    },
    {
      "location": "Definition 1.14",
      "doc1": {
        "content": "' Card Transaction ' means transaction effected by the use of Debit Card for both local and overseas transactions; face-to-face Card Present Transactions as well as non-face-to-face Card- Not-Present Transactions and Contactless Transactions (where applicable)."
      },
      "doc2": {
        "content": "'Transaksi Kad' bermaksud transaksi yang dilaksanakan dengan menggunakan Kad Debit untuk urus niaga tempatan dan luar negara; Transaksi dengan Kad secara bersemuka sertaTransaksi Tanpa Kad dan Transaksi Tanpa Sentuhan secara tidak bersemuka (di mana berkenaan)."
      },
      "discrepancies": [
        "1. 'Card Present Transactions as well as non-face-to-face Card-Not-Present Transactions and Contactless Transactions (where applicable)' is translated as 'Transaksi dengan Kad secara bersemuka sertaTransaksi Tanpa Kad dan Transaksi Tanpa Sentuhan secara tidak bersemuka (di mana berkenaan)'. The phrase 'Card-Not-Present Transactions' is translated as 'Transaksi Tanpa Kad', which omits the 'Not-Present' nuance.",
        "2. 'Contactless Transactions (where applicable)' is translated as 'Transaksi Tanpa Sentuhan secara tidak bersemuka (di mana berkenaan)', which adds 'secara tidak bersemuka' (non-face-to-face), not present in English."
      ],
      "explanation": "BM version omits the nuance of 'Not-Present' and adds 'non-face-to-face' for Contactless Transactions."
    },
    {
      "location": "Definition 1.20",
      "doc1": {
        "content": "' Character Card ' refers to the Debit Card with customized designs issued by the Bank such as Hello Kitty, Transformers and etc."
      },
      "doc2": {
        "content": "'Kad Karakter' merujuk kepada Kad Debit seperti Kad Debit Hello Kitty atau Transformers yang dikeluarkan oleh Bank."
      },
      "discrepancies": [
        "1. 'with customized designs' is omitted in BM version.",
        "2. 'such as Hello Kitty, Transformers and etc.' is translated as 'seperti Kad Debit Hello Kitty atau Transformers', omitting 'and etc.'"
      ],
      "explanation": "BM version omits 'customized designs' and 'etc.'"
    },
    {
      "location": "Definition 1.22",
      "doc1": {
        "content": "' Daily  Online  Purchase  Limit ' means  the  daily  maximum  permissible  Online  Purchase  Limit prescribed by the Bank under Clause 12.4 herein."
      },
      "doc2": {
        "content": "' Had  Belian  Dalam  Talian  Harian ' bermaksud  had  maksimum  belian  harian  dalam  talian dibenarkan yang ditetapkan oleh Bank dalam Klausa 12.4 di sini."
      },
      "discrepancies": [
        "1. 'permissible' is omitted in BM version.",
        "2. 'prescribed by the Bank under Clause 12.4 herein' is translated as 'yang ditetapkan oleh Bank dalam Klausa 12.4 di sini' (acceptable)."
      ],
      "explanation": "BM version omits 'permissible'."
    },
    {
      "location": "Definition 1.25",
      "doc1": {
        "content": "' Debit Card ' means the Hong Leong MyDebit/Visa/Mastercard Debit Card issued by the Bank."
      },
      "doc2": {
        "content": "'Kad Debit' bermaksud Kad Debit MyDebit/Visa/Mastercard Hong Leong yang dikeluarkan oleh Bank."
      },
      "discrepancies": [
        "1. 'Hong Leong' is placed after 'MyDebit/Visa/Mastercard' in BM version, changing the order.",
        "2. 'Debit Card' is translated as 'Kad Debit' (acceptable)."
      ],
      "explanation": "BM version changes the order of 'Hong Leong' and card brands."
    },
    {
      "location": "Definition 1.26",
      "doc1": {
        "content": "' DCC ' means  Dynamic  Currency  Conversion,  an  optional  service  offered  by  certain  overseas merchants or available for certain Overseas Transaction as defined under Clause 20.1 below (including ATM Card Transactions), which provides a choice to pay/withdraw cash in Ringgit Malaysia (including Card Transactions quoted in foreign currency), as elaborated further under Clause 20."
      },
      "doc2": {
        "content": "' DCC ' merujuk  kepada  Penukaran  Mata  Wang  Dinamik,  iaitu  perkhidmatan  pilihan  yang ditawarkan  oleh  peniaga  atau  tersedia  untuk  pembelian  luar  negara  tertentu  seperti  yang ditentukan dalam Klausa 20.1 di bawah (termasuk Transaksi Kad ATM), yang memberi pilihan pembayaran / pengeluaran tunai dalam Ringgit Malaysia (termasuk pembelian di luar negara dan pembelian dalam talian dalam mata wang asing) untuk transaksi luar negara, sebagaimana yang dihuraikan dalam Klausa 20."
      },
      "discrepancies": [
        "1. 'certain overseas merchants' is translated as 'peniaga', omitting 'overseas'.",
        "2. 'certain Overseas Transaction' is translated as 'pembelian luar negara tertentu', omitting 'Transaction' and using 'pembelian' (purchase) instead.",
        "3. 'including ATM Card Transactions' is translated as 'termasuk Transaksi Kad ATM' (acceptable).",
        "4. 'provides a choice to pay/withdraw cash in Ringgit Malaysia (including Card Transactions quoted in foreign currency)' is translated as 'yang memberi pilihan pembayaran / pengeluaran tunai dalam Ringgit Malaysia (termasuk pembelian di luar negara dan pembelian dalam talian dalam mata wang asing) untuk transaksi luar negara', which adds 'pembelian dalam talian' (online purchase) and omits 'Card Transactions quoted in foreign currency'."
      ],
      "explanation": "BM version omits 'overseas' for merchants, changes 'Transaction' to 'pembelian', and adds 'online purchase' not present in English."
    },
    {
      "location": "Definition 1.27",
      "doc1": {
        "content": "' Fee ' means fees payable at application, yearly or such other intervals as may be determined by the Bank, by the Cardholder for the utilization of the Services which shall be debited from the Account on each anniversary date of the issuance of the Debit Card and shall also include all other fees, service charges,  commissions  and  other  payments  charged  by  the  Bank  under  these  T&amp;Cs.  The  Bank reserves  the  right  to  vary  the  Fee  by  giving twenty-one  (21) calendar  days'  prior  notice  to  the Cardholder."
      },
      "doc2": {
        "content": "'Fi' termasuk fi perlu dibayar oleh Pemegang Kad semasa permohonan, tahunan atau sebarang jarak waktu yang mungkin ditentukan oleh Bank untuk menggunakan Perkhidmatan yang akan didebit dari  Akaun pada setiap tarikh ulangtahun Kad Debit dikeluarkan dan akan merangkumi semua fi lain, caj perkhidmatan, komisen dan lain-lain bayaran yang dicaj oleh Bank di bawah T&amp;S ini. Bank berhak untuk mengubah Fi dengan memberi notis awal dua puluh satu (21) hari kalendar terlebih dahulu kepada Pemegang Kad."
      },
      "discrepancies": [
        "1. 'payable at application, yearly or such other intervals as may be determined by the Bank' is translated as 'perlu dibayar oleh Pemegang Kad semasa permohonan, tahunan atau sebarang jarak waktu yang mungkin ditentukan oleh Bank', omitting 'by the Cardholder for the utilization of the Services'.",
        "2. 'debited from the Account on each anniversary date of the issuance of the Debit Card' is translated as 'didebit dari Akaun pada setiap tarikh ulangtahun Kad Debit dikeluarkan' (acceptable).",
        "3. 'shall also include all other fees, service charges, commissions and other payments charged by the Bank under these T&Cs' is translated as 'akan merangkumi semua fi lain, caj perkhidmatan, komisen dan lain-lain bayaran yang dicaj oleh Bank di bawah T&S ini' (acceptable).",
        "4. 'The Bank reserves the right to vary the Fee by giving twenty-one (21) calendar days' prior notice to the Cardholder.' is translated as 'Bank berhak untuk mengubah Fi dengan memberi notis awal dua puluh satu (21) hari kalendar terlebih dahulu kepada Pemegang Kad.' (acceptable)."
      ],
      "explanation": "BM version omits 'by the Cardholder for the utilization of the Services'."
    },
    {
      "location": "Definition 1.36",
      "doc1": {
        "content": "' MCF Enabled Account ' means the Account of the Cardholder where the MCF (as defined under Clause 1.45 herein) has been enabled, which may include a Retail Purchase Account."
      },
      "doc2": {
        "content": "' Akaun Diaktifkan MCF' bermaksud Akaun Pemegang Kad di mana MCF (seperti yang ditakrifkan dalam Klausa 1.45 di sini) telah diupayakan, yang mungkin termasuk akaun yang dipautkanke Kad Debit. telah diaktifkan, yang mungkin termasuk Akaun Pembelian Runcit."
      },
      "discrepancies": [
        "1. 'which may include a Retail Purchase Account' is translated as 'yang mungkin termasuk akaun yang dipautkanke Kad Debit. telah diaktifkan, yang mungkin termasuk Akaun Pembelian Runcit.' which is a duplicated and fragmented translation.",
        "2. 'dipautkanke' is a spelling error; should be 'dipautkan ke'."
      ],
      "explanation": "BM version contains a duplicated and fragmented translation and a spelling error."
    },
    {
      "location": "Definition 1.41",
      "doc1": {
        "content": "' MyKad ' means the card issued to the Cardholder by the Malaysian National Registration Department to identify and verify the identity of the Cardholder."
      },
      "doc2": {
        "content": "'MyKad' bermaksud kad yang dikeluarkan kepada Pemegang Kad oleh Jabatan Pendaftaran Negara  Malaysia  kepada  Pemegang  Kad  untuk  mengenalpasti  and  megesahkan  identiti Pemegang Kad."
      },
      "discrepancies": [
        "1. 'to identify and verify the identity of the Cardholder' is translated as 'untuk mengenalpasti and megesahkan identiti Pemegang Kad'.",
        "2. 'and' is left untranslated as 'and' instead of 'dan'.",
        "3. 'megesahkan' is a spelling error; should be 'mengesahkan'."
      ],
      "explanation": "BM version contains a language mixing error ('and') and a spelling error ('megesahkan')."
    },
    {
      "location": "Definition 1.43",
      "doc1": {
        "content": "' Multi-Currency Debit Card ' or ' MCF Card ' or ' Hong Leong Visa Multi Currency Debit Card ' refers to the Debit Card with black colour base issued by the Bank to Hong Leong Pay&amp;Save accountholders wherein the Hong Leong Pay&amp;Save accountholders can only tag the Retail Purchase Account to Hong Leong Pay&amp;Save account."
      },
      "doc2": {
        "content": "' Kad  Debit  Multi  Currency' atau 'Kad  MCF' atau 'Kad  Debit  Multi  Currency  Visa  Hong Leong' merujuk kepada Kad Debit dengan asas warna hitam yang dikeluarkan oleh Bank kepada pemegang Akaun Pay&amp;Save Hong Leong dan hanya boleh dipautkan kepada Akaun Pembelian Runcit ke Akaun Pay&amp;Save Hong Leong."
      },
      "discrepancies": [
        "1. 'can only tag the Retail Purchase Account to Hong Leong Pay&Save account' is translated as 'hanya boleh dipautkan kepada Akaun Pembelian Runcit ke Akaun Pay&Save Hong Leong', which omits the restriction that only Pay&Save accountholders can do this.",
        "2. 'black colour base' is translated as 'asas warna hitam' (acceptable)."
      ],
      "explanation": "BM version omits the restriction that only Pay&Save accountholders can tag the Retail Purchase Account."
    },
    {
      "location": "Definition 1.44",
      "doc1": {
        "content": "' Multi-Currency  Feature ' or ' MCF ' refers  to  the  foreign  currency  wallet  within  an  Account approved by the Bank for MCF which allows the Cardholder to, amongst others: (a) hold foreign currencies approved by the Bank from time to time; (b) perform Overseas Transactions in the foreign currency selected by the Cardholder; (c) convert one (1) foreign currency to another foreign currency in the Cardholder's MCF Enabled Account via the Bank's branches or HLB Connect."
      },
      "doc2": {
        "content": "' Ciri Mata Wang Pelbagai ' atau ' MCF ' bermaksud mata wang asing yang disimpan dalam Akaun yang dibenarkan oleh Bank untuk MCF yang membolehkan Pemegang Kad, antara lain: (a) memegang mata wang asing yang dibenarkan oleh Bank dari semasa ke semasa; (b) melakukan Transaksi Luar Negara dalam mata wang asing yang dipilih oleh Pemegang Kad; (c) menukar satu (1) mata wang asing ke mata wang asing yang lain dalam Akaun Diaktifkan MCF Pemegang Kad melalui cawangan Bank atau Hong Leong Connect."
      },
      "discrepancies": [
        "1. 'foreign currency wallet within an Account' is translated as 'mata wang asing yang disimpan dalam Akaun', omitting the concept of 'wallet'.",
        "2. 'approved by the Bank for MCF' is translated as 'yang dibenarkan oleh Bank untuk MCF' (acceptable)."
      ],
      "explanation": "BM version omits the concept of 'wallet' and only refers to 'mata wang asing yang disimpan dalam Akaun'."
    },
    {
      "location": "Definition 1.45",
      "doc1": {
        "content": "' Notifications via HLB Connect App ' means a push notification feature that allows the Cardholder to receive the Card notifications via the HLB Connect App."
      },
      "doc2": {
        "content": "'Paparan  Notifikasi  HLB  Connect  App' bermaksud  ciri  notifikasi  tolak  yang  membolehkan Pemegang Kad menerima notifikasi melalui HLB Connect App."
      },
      "discrepancies": [
        "1. 'Notifications via HLB Connect App' is translated as 'Paparan Notifikasi HLB Connect App', which omits 'via' and uses 'Paparan' (display) instead of 'Pemberitahuan' (notification).",
        "2. 'the Card notifications' is translated as 'notifikasi' (notification), omitting 'Card'."
      ],
      "explanation": "BM version omits 'Card' in 'Card notifications' and uses 'Paparan' instead of 'Pemberitahuan'."
    },
    {
      "location": "Definition 1.46",
      "doc1": {
        "content": "' One-Time Password (OTP) ' means a unique, single-use 6-digit code that is sent via SMS or Card OTP in HLB Connect App to perform certain online transactions or actions;"
      },
      "doc2": {
        "content": "' One-Time Password (OTP )'  bermaksud kod 6-digit yang unik dan sekali guna yang dihantar melalui SMS atau Kad OTP dalam Aplikasi HLB Connect untuk melakukan transaksi dalam talian tertentu atau tinkdakan."
      },
      "discrepancies": [
        "1. 'actions' is translated as 'tinkdakan', which is a spelling error; should be 'tindakan'."
      ],
      "explanation": "BM version contains a spelling error: 'tinkdakan' instead of 'tindakan'."
    },
    {
      "location": "Definition 1.49",
      "doc1": {
        "content": "' PIN ' means a numeric code that acts as a password that is used to authenticate a Cardholder to their account."
      },
      "doc2": {
        "content": "'PIN' bermaksud  kod  berangka  yang  bertindak  sebagai  kata  laluan  yang  digunakan  untuk mengesahkan Pemegang Kad ke akaun mereka"
      },
      "discrepancies": [
        "1. Missing period at the end of the BM sentence.",
        "2. 'to their account' is translated as 'ke akaun mereka' (acceptable)."
      ],
      "explanation": "BM version omits the period at the end of the sentence."
    },
    {
      "location": "Definition 1.55",
      "doc1": {
        "content": "' Retail  Transaction '  means  all  purchase  of  goods  or  services  charged  to  the  Debit  Card  at  the Authorised  Merchant  where  the  Debit  Card  can  be  accepted  for  payment  locally  and  overseas including  Online  Purchases,  Touch  'n  Go  auto-reload,  Petrol  Purchases,  auto-billing/recurring transactions  and  excluding  cash  withdrawals,  fund  transfer,  annual  fees  payment  and  other Services/miscellaneous fees as defined by the Bank from time to time with prior notice."
      },
      "doc2": {
        "content": "\"Transaksi Runcit\" bermaksud transaksi yang menggunakan Kad Debit di Peniaga Sah di mana Kad Debit boleh diterima untuk pembayaran di dalam dan luar negara termasuk Pembelian Dalam Talian, tambah nilai Touch 'n Go secara automatik, Pembelian Petrol, Auto Bill/transaksi urusniaga yang berulang dan tidak termasuk pengeluaran wang tunai, pemindahan dana, pembayaran yuran tahunan dan perkhidmatan lain/yuran pelbagai seperti yang ditakrifkan oleh Bank dari semasa ke semasa dengan memberi notis terlebih dahulu."
      },
      "discrepancies": [
        "1. 'all purchase of goods or services charged to the Debit Card' is translated as 'transaksi yang menggunakan Kad Debit', omitting 'charged to'.",
        "2. 'auto-billing/recurring transactions' is translated as 'Auto Bill/transaksi urusniaga yang berulang', which adds 'Auto Bill' as a term.",
        "3. 'other Services/miscellaneous fees' is translated as 'perkhidmatan lain/yuran pelbagai', omitting 'Services' as a capitalized term."
      ],
      "explanation": "BM version omits 'charged to', adds 'Auto Bill', and omits capitalization of 'Services'."
    },
    {
      "location": "Definition 1.57",
      "doc1": {
        "content": "' Security Codes ' means the security codes given by the Bank to the Cardholder for access to the respective Services comprising of the PIN (for ATM Services), IPIN (for Hong Leong Connect), HLB Connect Code (for Hong Leong Connect), and includes any other user name, password, personal identification number, digital certificate or any other security codes as the Bank may issue from time to time for access to all or any of the Services and reference to the term 'Security Codes' shall mean the security code or codes relevant to the respective Services as the context shall require."
      },
      "doc2": {
        "content": "'Kod Keselamatan' bermaksud kod keselamatan yang diberikan oleh Bank kepada Pemegang Kad untuk mengakses Perkhidmatan berkaitan yang merangkumi PIN (untuk Perkhidmatan ATM), IPIN (untuk Hong Leong Connect), HLB Connect Code (untuk Hong Leong Connect) dan termasuk lain-lain nama pengguna, kata laluan, nombor pengenalan peribadi, sijil digital atau lain-lain kod keselamatan  yang  mungkin  dikeluarkan  oleh  Bank  dari  semasa  ke  semasa  untuk  mengakses semua atau mana-mana Perkhidmatan dan rujukan untuk terma 'Kod Keselamatan' akanbermaksud kod atau kod-kod keselamatan berkaitan dengan Perkhidmatan tersebut sebagaimanadiperlukan."
      },
      "discrepancies": [
        "1. 'comprising of the PIN (for ATM Services), IPIN (for Hong Leong Connect), HLB Connect Code (for Hong Leong Connect)' is translated as 'yang merangkumi PIN (untuk Perkhidmatan ATM), IPIN (untuk Hong Leong Connect), HLB Connect Code (untuk Hong Leong Connect)' (acceptable).",
        "2. 'any other user name, password, personal identification number, digital certificate or any other security codes' is translated as 'lain-lain nama pengguna, kata laluan, nombor pengenalan peribadi, sijil digital atau lain-lain kod keselamatan' (acceptable).",
        "3. 'reference to the term 'Security Codes' shall mean the security code or codes relevant to the respective Services as the context shall require.' is translated as 'rujukan untuk terma 'Kod Keselamatan' akanbermaksud kod atau kod-kod keselamatan berkaitan dengan Perkhidmatan tersebut sebagaimanadiperlukan.'",
        "4. 'akanbermaksud' and 'sebagaimanadiperlukan' are spelling errors; should be 'akan bermaksud' and 'sebagaimana diperlukan'."
      ],
      "explanation": "BM version contains two spelling errors: 'akanbermaksud' and 'sebagaimanadiperlukan'."
    },
    {
      "location": "Definition 1.61",
      "doc1": {
        "content": "' Tax '  means  any  present  or  future,  direct  or  indirect,  Malaysian  or  foreign  tax,  levy,  impost,  duty, charge, fee,  deduction or  withholding  of  any  nature,  that  is  imposed  by  any  Appropriate  Authority, including, without limitation, any consumption tax and other taxes by whatever name called, and any interest, fines or penalties in respect thereof."
      },
      "doc2": {
        "content": "\" Cukai \" bermaksud sebarang cukai semasa atau masa hadapan, langsung atau tidak langsung, cukai,  levi,  impos,  duti,  caj,  yuran,  sebarang  bentuk  potongan  atau  pegangan  dalam sebarang bentuk, Malaysia atau asing, yang dikenakan oleh Pihak Berkuasa Berkenaan, termasuk tanpa had, sebarang cukai penggunaan dan lain-lain cukai dengan apa sahaja nama yang dipanggil, dan sebarang faedah, denda atau penalti yang berkenaan dengannya."
      },
      "discrepancies": [
        "1. 'deduction or withholding of any nature' is translated as 'sebarang bentuk potongan atau pegangan dalam sebarang bentuk', which is repetitive.",
        "2. 'Malaysian or foreign tax' is translated as 'Malaysia atau asing', omitting the word 'tax' after 'asing'."
      ],
      "explanation": "BM version is repetitive in 'sebarang bentuk potongan atau pegangan dalam sebarang bentuk' and omits 'tax' after 'asing'."
    },
    {
      "location": "Definition 1.65",
      "doc1": {
        "content": "Words  importing  the  singular  shall  include  plural  number  and  vice  versa  and  those  importing  the masculine gender shall include the feminine and neuter gender and vice versa."
      },
      "doc2": {
        "content": "Perkataan yang bermaksud tunggal juga bermaksud majmuk dan sebaliknya serta serta perkataan yang bermaksud jantina maskulin hendaklah termasuk jantina feminin dan neuter dan sebaliknya."
      },
      "discrepancies": [
        "1. 'serta serta' is a word repetition error; should be 'serta'."
      ],
      "explanation": "BM version contains a word repetition error: 'serta serta'."
    },
    {
      "location": "Section 2.0, Clause 2.2(a)",
      "doc1": {
        "content": "That  the  Security  Codes  must  be  kept  secret  and  the  Security  Code  once  received  by  the Cardholder must be changed immediately after the Cardholder has received and read them and may only be used by the Cardholder and no one else. If a Security Code is not issued to the Cardholder, the Cardholder will be advised to create his/her own Security Code as a condition for access to the Services."
      },
      "doc2": {
        "content": "Kod  Keselamatan  hendaklah  dirahsiakan  dan  apabila  Pemegang  Kad  menerima  Kod Keselamatan ia hendaklah ditukar sertamerta apabila telah diterima dan dibaca, dan hanya boleh digunakan oleh Pemegang Kad sahaja dan bukan orang lain. Jika Kod Keselamatan tidak dikeluarkan kepada Pemegang Kad, Pemegang Kad dinasihatkan agar mencipta Kod Keselamatan sendiri sebagai syarat untuk mengakses Perkhidmatan."
      },
      "discrepancies": [
        "1. 'immediately' is translated as 'sertamerta', which is a spelling error; should be 'serta-merta'."
      ],
      "explanation": "BM version contains a spelling error: 'sertamerta' instead of 'serta-merta'."
    },
    {
      "location": "Section 2.0, Clause 2.2(c)",
      "doc1": {
        "content": "The Cardholder must not disclose the Security Code to any person under any circumstances or by any means whether voluntarily or otherwise and must take all care to prevent the Security Code from becoming known to any other person. The Cardholder understands and agrees that failure to comply with this requirement may expose the Cardholder to the consequences of theft and/or unauthorised use of the Debit Card, for which the Bank will not be liable. The Cardholder must report a breach of Security Code or the loss of a Security Code to the Bank as soon as reasonably practicable, upon the Cardholder becoming aware of the breach or loss respectively. The Cardholder hereby undertakes to reimburse and pay the Bank on the Bank's written demand all claims and liabilities incurred by the Bank arising from such unauthorised use."
      },
      "doc2": {
        "content": "Pemegang Kad tidak  boleh  mendedahkan  Kod  Keselamatan  kepada  mana-mana  pihak  di bawah  apa  jua  sebab  atau  cara  sama  ada  secara  sukarela  atau  sebaliknya  dan  harus mengambil segala langkah wajar untuk mencegah Kod Keselamatan daripada diketahui oleh pihak  lain.  Pemegang  Kad  memahami  dan  bersetuju  bahawa  kegagalan  untuk  mematuhi peraturan ini boleh mendedahkan  Pemegang  Kad  kepada  akibat  kecurian dan/atau penggunaan tanpa kebenaran  Kad Debit,  yang  mana  Bank  tidak  akan  bertanggungjawab. Pemegang Kad mesti melaporkan sebarang pelanggaran Kod Keselamatan atau kehilangan Kod  Keselamatan  kepada  Bank  dengan  secepat  yang  mungkin,  apabila  Pemegang  Kad menyedari  tentang  pelanggaran  atau  kerugian  masing-masing.  Pemegang  Kad  dengan  ini bersetuju untuk membayar balik dan membayar kepada Bank atas permintaan bertulis Bank semua tuntutan  dan  liabiliti  yang  ditanggung  oleh  Bank  yang  timbul  daripada  penggunaan tanpa kebenaran tersebut."
      },
      "discrepancies": [
        "1. 'as soon as reasonably practicable' is translated as 'dengan secepat yang mungkin', omitting 'reasonably practicable'."
      ],
      "explanation": "BM version omits 'reasonably practicable' and only uses 'as soon as possible'."
    },
    {
      "location": "Section 2.0, Clause 2.2(k)",
      "doc1": {
        "content": "The Debit Card is valid only up to the Good Thru Date. The renewal letter to the Cardholder will be mailed out thirty (30) days prior to the Good Thru Date. The Bank will mail a renewal letter to the Cardholder to inform the Cardholder to proceed to the nearest branch or any of the Bank's branches for collection of the replacement Debit Card. The Cardholder shall ensure that as soon as the Debit Card expires, it is destroyed, by cutting it diagonally in half and to return it to the Bank for replacement of the Debit Card."
      },
      "doc2": {
        "content": "Kad Debit adalah sah sehingga Tarikh Baik Sehingga. Surat pembaharuan kepada Pemegang Kad akan dikirimkan tiga puluh (30) hari sebelum Tarikh Baik Sehingga. Bank akan mengirim surat  pembaharuan  kepada  Pemegang  Kad  untuk  memaklumkan  Pemegang  Kad  untuk mengunjungi  cawangan  Bank  yang  terdekat  atau  mana-mana  cawangan  Bank  untuk memperolehi  Kad  Debit  Penggantian.  Pemegang  Kad  harus  memastikan  bahawa  sebaik sahaja  Kad  Debit  luput,  ia  dimusnahkan,  dengan  memotong  dua  secara  melintang  dan mengembalikannya kepada Bank untuk penggantian Kad Debit."
      },
      "discrepancies": [
        "1. 'cutting it diagonally in half' is translated as 'memotong dua secara melintang', which means 'cutting in half horizontally', not 'diagonally'."
      ],
      "explanation": "BM version translates 'diagonally' as 'melintang' (horizontally), which is inaccurate."
    },
    {
      "location": "Section 2.0, Clause 2.2(m)",
      "doc1": {
        "content": "The Cardholder shall not use the Debit Card for withdrawal of cash, payment or fund transfer unless  there  are  sufficient  funds  in  the  Account.  Any  withdrawal  of  cash,  payment  or  fund transfer shall be rejected if there are insufficient funds in the Account."
      },
      "doc2": {
        "content": "Pemegang Kad tidak boleh menggunakan Kad Debit untuk pengeluaran tunai, bayaran atau pemindahan  dana  melainkan  terdapat  dana  yang  mencukupi  di  dalam  Akaun.  Sebaran pengeluaran tunai, bayaran atau pindahan dana akan ditolak jika tidak terdapat dana yang mencukupi di dalam Akaun."
      },
      "discrepancies": [
        "1. 'Sebaran pengeluaran tunai' is a spelling/word error; should be 'Sebarang pengeluaran tunai'."
      ],
      "explanation": "BM version contains a spelling/word error: 'Sebaran' instead of 'Sebarang'."
    },
    {
      "location": "Section 2.0, Clause 2.2(o)",
      "doc1": {
        "content": "If the Bank finds, suspects or has reasons to believe that the Debit Card has been used for any unlawful activity, the Bank may take any action considered appropriate to meet any obligation in connection with the  prevention  of  any  unlawful  activity  including  but  not  limited  to  fraud,  money  laundering, terrorist activity/financing, bribery, corruption and/or tax evasion."
      },
      "doc2": {
        "content": "Jika Bank mendapati, mengesyaki atau mempunyai sebab untuk mempercayai  bahawa  Kad  Debit  telah  digunakan  untuk  sebarang  aktiviti  yang  menyalahi undang-undang, Bank boleh mengambil apa-apa tindakan dianggap sesuai untuk memenuhi apa-apa kewajipan yang berkaitan dengan pencegahan apa-apa aktiviti haram termasuk tetapi tidak  terhad  kepada  penipuan,  pengubahan  wang  haram,  aktiviti/pembiayaan  pengganas, rasuah, penyalahgunaan wang dan/atau pengelakan cukai."
      },
      "discrepancies": [
        "1. 'terrorist activity/financing' is translated as 'aktiviti/pembiayaan pengganas', which is acceptable.",
        "2. 'bribery, corruption' is translated as 'rasuah, penyalahgunaan wang', which adds 'penyalahgunaan wang' (misuse of money) instead of 'corruption'."
      ],
      "explanation": "BM version translates 'corruption' as 'penyalahgunaan wang' (misuse of money), which is not equivalent."
    },
    {
      "location": "Section 2.0, Clause 2.2(t)",
      "doc1": {
        "content": "The Cardholder  who  wishes to  opt-out  from  the  sharing  of  his/her  personal  data  within  the Bank's  and/or  Hong  Leong  Financial  Group  Berhad  group  of  companies  for  marketing  and promotional purposes is required to visit any of the Bank's branches or call the Bank's Contact Centre at 03-7626 8899 to register his/her instruction to opt-out of the said sharing."
      },
      "doc2": {
        "content": "Pemegang Kad yang ingin dikecualikan daripada pekongsian data peribadi mereka di dalam Bank dan/atau kumpulan syarikat Hong Leong Financial Group Berhad bagi tujuan pemasaran dan  promosi  perlu  mengunjungi  mana-mana  cawangan  Bank  atau  menghubungi  Pusat Panggilan  Bank  di 03-7626  8899 untuk  mendaftar  permintaan  mengecualikan  pekongsian tersebut."
      },
      "discrepancies": [
        "1. 'opt-out' is translated as 'dikecualikan', which is not the same as 'opt-out'.",
        "2. 'register his/her instruction to opt-out of the said sharing' is translated as 'mendaftar permintaan mengecualikan pekongsian tersebut', which is acceptable."
      ],
      "explanation": "BM version uses 'dikecualikan' (to be exempted) instead of 'opt-out', which is not equivalent."
    },
    {
      "location": "Section 3.0, Clause 3.2",
      "doc1": {
        "content": "Contactless Transactions without PIN verification is capped at Ringgit Malaysia Two Hundred Fifty (RM250)  per  transaction  (' Contactless  Transaction  Limit ').  The  Cardholder  will  be  required  to perform  PIN  verification  for  Contactless  Transactions  above  Ringgit  Malaysia  Two  Hundred  Fifty (RM250)."
      },
      "doc2": {
        "content": "Transaksi Tanpa Sentuhan tanpa pengesahan PIN dihadkan kepada Ringgit Malaysia Dua Ratus Lima Puluh (RM250) setiap transaksi (' Had Transaksi Tanpa Sentuhan '). Pemegang Kad akan dikehendaki mengesahkan PIN bagi Transaksi Tanpa Sentuhan melebihi Ringgit Malaysia Dua Ratus Lima Puluh (RM250)."
      },
      "discrepancies": [
        "1. 'is capped at' is translated as 'dihadkan kepada', omitting the nuance of 'maximum limit'."
      ],
      "explanation": "BM version omits the nuance of 'maximum limit' in 'is capped at'."
    },
    {
      "location": "Section 4.0, Clause 4.2",
      "doc1": {
        "content": "To complete the Cardholder's online purchases, the Cardholder is required to: (i) Check Debit Card OTP via HLB Connect App or SMS; and (ii) Enter the 6-digit OTP code on the Merchant's payment page"
      },
      "doc2": {
        "content": "Untuk melengkapkan pembelian dalan talian, Pemegang Kad dikehendaki:: (i) Semak Kad Debit OTP melalui HLB Connect App atau SMS; dan (ii) Masukkan kod OTP 6-digit pada halaman pembayaran Peniaga"
      },
      "discrepancies": [
        "1. 'dalan talian' is a spelling error; should be 'dalam talian'.",
        "2. Double colon 'dikehendaki::' is a punctuation error; should be single colon.",
        "3. 'on the Merchant's payment page' is translated as 'pada halaman pembayaran Peniaga', omitting 'Merchant's' possessive nuance."
      ],
      "explanation": "BM version contains a spelling error, a punctuation error, and omits the possessive nuance."
    },
    {
      "location": "Section 5.0, Clause 5.1",
      "doc1": {
        "content": "The  Statement  will  be  incorporated  in  the  passbook/statement  of  the  Cardholder's  designated Savings/Savings Account-i or Current Account/Current Account-i (' CASA/CASA-i ') and the Cardholder can view his/her Statement for free via HLB Connect which consists, amongst others, the Card Transaction and Posting Date of the Card Transactions performed by the Cardholder for the relevant period stated."
      },
      "doc2": {
        "content": "Penyata  akan  dikemas  kini  ke  dalam  penyata/buku  Akaun  Simpanan/Akaun  Simpanan-i  atau Akaun  Semasa/Akaun  Semasa-i  yang  ditetapkan,  dan  Pemegang  Kad  boleh  menyemak Penyatanya secara percuma melalui Hong Leong Connect yang meliputi, antara lain, Transaksi Kad dan Tarikh Pengeposan Transaksi Kad yang dilakukan oleh Pemegang Kad untuk tempoh yang dinyataka."
      },
      "discrepancies": [
        "1. 'CASA/CASA-i' is omitted in BM version.",
        "2. 'the relevant period stated' is translated as 'tempoh yang dinyataka', which is a spelling error; should be 'dinayatakan'."
      ],
      "explanation": "BM version omits 'CASA/CASA-i' and contains a spelling error."
    },
    {
      "location": "Section 5.0, Clause 5.2",
      "doc1": {
        "content": "The printed monthly Statement shall indicate all the Card Transactions, Posting Date and Transaction Date for the relevant month. The Cardholder may request for an ad hoc printed Statement and the Bank shall levy a service fee of Ringgit Malaysia Ten (RM10) plus Ringgit Malaysia Two (RM2) per page for Statement up to one (1) year ago or Ringgit Malaysia Ten (RM10) plus Ringgit Malaysia Five (RM5) per page for Statement more than one (1) year ago per request."
      },
      "doc2": {
        "content": "Penyata bulanan yang dicetak menunjukkan semua TransaksiKad, Tarikh  Pengeposan  dan  Tarikh  Transaksi  untuk  bulan  yang  berkenaan.  Pemegang  Kad  boleh meminta Penyata dicetak pada bila-bila masa dan Bank akan mengenakan bayaran perkhidmatan sebanyak Ringgit Malaysia Sepuluh (RM10) dan Ringgit Malaysia Dua (RM2) bagi setiap halaman untuk  Penyata  sehingga satu  (1) tahun  yang  lalu  atau  Ringgit  Malaysia  Sepuluh  (RM10)  dan Ringgit Malaysia Lima (RM5) bagi setiap halaman untuk Penyata lebih daripada satu (1) tahun yang lalu untuk setiap permintaan."
      },
      "discrepancies": [
        "1. 'ad hoc printed Statement' is omitted in BM version.",
        "2. 'plus' is translated as 'dan', which may cause confusion as it could be interpreted as a total rather than an addition."
      ],
      "explanation": "BM version omits 'ad hoc' and uses 'dan' instead of 'plus'."
    },
    {
      "location": "Section 5.0, Clause 5.3",
      "doc1": {
        "content": "The records and entries in the Account with the Bank which appears on the monthly Statement shall be deemed to be correct and binding on the Cardholder unless written notice to the contrary is given to the Bank by the Cardholder within fourteen (14) days after the receipt of the Statement."
      },
      "doc2": {
        "content": "Rekod  dan  catatan  dalam  Akaun  yang  ditetapkan  dengan  Bank  yang  terdapat  pada  Penyata bulanan akan dianggap sebagai tepat dan mengikat ke atas Pemegang Kad kecuali makluman bertulis  bertentangan dengannya diberi oleh Pemegang Kad kepada Bank dalam masa empat belas (14) hari kalendar selepas menerima."
      },
      "discrepancies": [
        "1. 'after the receipt of the Statement' is translated as 'selepas menerima', omitting 'the Statement'."
      ],
      "explanation": "BM version omits 'the Statement' after 'selepas menerima'."
    },
    {
      "location": "Section 5.0, Clause 5.4",
      "doc1": {
        "content": "If the Cardholder for any reason whatsoever does not, within fourteen (14) days, notify the Bank in writing  of  any  error  in  the  Statement,  and  in  the  absence  of  any  obvious  error  on  the  face  of  the statement or fraud by the Bank then the Cardholder shall be deemed to have accepted the records and entries in the Statement as correct, final and conclusive. The Statement shall be considered conclusive and binding on the Cardholder and the Cardholder's legal representatives and successors."
      },
      "doc2": {
        "content": "Jika atas sebarang sebab Pemegang Kad tidak memaklumkan kepada Bank secara bertulis dalam masa empat belas (14) hari tentang sebarang percanggahan di dalam Penyata dan sekiranya tiada  sebarang  kesilapan  yang  jelas  pada  muka  penyata  atau  penipuan  oleh  Bank,maka PemegangKad akan dianggap telah menerima rekod dan catatan di dalam Penyata sebagai betul, akhir danmuktamad. Penyata itu harus dianggap sebagai muktamad dan terikat kepada Pemegang Kad,  wakil  perundangan  dan  pengganti  Pemegang  Kad,  dan  sebarang  tuntutan  atau  dakwa terhadap Bank yang mendakwa Penyata itu adalah salah adalah tidak sah."
      },
      "discrepancies": [
        "1. 'any error in the Statement' is translated as 'sebarang percanggahan di dalam Penyata', which omits 'error' and uses 'percanggahan' (discrepancy).",
        "2. 'the Cardholder's legal representatives and successors' is translated as 'wakil perundangan dan pengganti Pemegang Kad', omitting 'the Cardholder's'.",
        "3. 'any claim or suit against the Bank alleging the Statement is incorrect shall be invalid' is added in BM version and not present in English."
      ],
      "explanation": "BM version uses 'percanggahan' instead of 'error', omits 'the Cardholder's' before 'legal representatives', and adds a sentence not present in English."
    },
    {
      "location": "Section 7.0, Clause 7.4",
      "doc1": {
        "content": "The Bank shall release the amounts on hold if the corresponding Card Transactions are not presented to the Bank for payment within such periods as the Bank deems fit. The Cardholder further expressly agrees that the Bank shall have the right to place a hold back onto the Retail Purchase Account and to debit the Retail Purchase Account if the Card Transactions are likely to be or are presented for payment subsequently by the Authorised Merchants upon expiry of twenty-one one (21) calendar days."
      },
      "doc2": {
        "content": "Bank hendaklah mengeluarkan jumlah yang ditahan jika Transaksi Kad yang sepadan tidak dikemukakan kepada Bank untuk pembayaran dalam tempoh yang dianggap sesuai oleh Bank. Pemegang Kad selanjutnya dengan nyata bersetuju bahawa Bank berhak untuk menahan Akaun Belian Runcit dan mendebit Akaun Belian Runcit jika Transaksi Kad berkemungkinan akan atau dibentangkan untuk pembayaran kemudiannya oleh Pedagang Dibenarkan apabila tamat tempoh dua  puluh  satu  satu  (21)  hari  kalendar."
      },
      "discrepancies": [
        "1. 'place a hold back onto the Retail Purchase Account' is translated as 'menahan Akaun Belian Runcit', omitting 'hold back' nuance.",
        "2. 'twenty-one one (21) calendar days' is translated as 'dua puluh satu satu (21) hari kalendar', which is a word repetition error."
      ],
      "explanation": "BM version omits 'hold back' nuance and contains a word repetition error."
    },
    {
      "location": "Section 8.0, Clause 8.1",
      "doc1": {
        "content": "The Cardholder fully understands that failure to take reasonable care and precaution in the safekeeping of the Debit Card may expose the Cardholder to the consequences of theft, loss and/or fraudulent use of the Debit Card. The Cardholder shall use all precautions to prevent or guard against such an event. If such an event occurs, the Cardholder shall: (i) If the event occurred in Malaysia - Upon discovery of such event, immediately notify the Bank via HLB Contact Centre at 03-76268899 or the National Scam Response Centre (NSRC) at 997. (ii) If the event occurred overseas - Notify Visa Travel Service Centre or any member of Mastercard or its nearest affiliates."
      },
      "doc2": {
        "content": "Pemegang Kad  harus  mengambil  segala  langkah  keselamatan  untuk  mengelakkan  Kad  Debit daripada kehilangan atau kecurian dan Pemegang Kad tidak boleh meninggalkan Kad Debit tanpa dijaga  atau  mendedahkan  PIN  dan/atau  butiran  Kad  Debit  kepada  mana-mana  pihak  ketiga. Sekiranya berlaku kehilangan dan/atau kecurian Kad Debit dan/atau pendedahan PIN dan/atau butiran  kepada  pihak  yang  tidak  dibenarkan,  Pemegang  Kad  apabila menyedarinya hendaklah memaklumkan kepada Bank dengan secepat yang munasabah boleh dilaksanakan selepas itu (jika perkara tersebut berlaku di Malaysia) atau Visa Travel Service Centre atau mana-mana ahli Mastercard atau sekutu terdekatnya (jika perkara tersebut berlaku di luar negara). Pemegang Kad memahami sepenuhnya bahawa kegagalan untuk menjaga dan mengambil langkah keselamatan yang munasabah dalam penyimpanan Kad Debit boleh mendedahkan Pemegang Kad kepada risiko kecurian dan/atau penggunaan tanpa kebenaran Kad Debit."
      },
      "discrepancies": [
        "1. 'immediately notify the Bank via HLB Contact Centre at 03-76268899 or the National Scam Response Centre (NSRC) at 997' is omitted in BM version.",
        "2. 'fraudulent use of the Debit Card' is translated as 'penggunaan tanpa kebenaran Kad Debit', omitting 'fraudulent'."
      ],
      "explanation": "BM version omits the specific notification instructions and omits 'fraudulent' in 'fraudulent use'."
    },
    {
      "location": "Section 8.0, Clause 8.6",
      "doc1": {
        "content": "The Cardholder would not be liable for unauthorised transactions which require PIN verification or signature verification or with contactless card, provided always that the Cardholder has not: (i) acted fraudulently; (ii) delayed in notifying the Bank as soon as reasonably after having discovered: (a) any loss or unauthorised use of the Card; or (b) any security breach of the Cardholder banking credentials or the loss of a security device; (iii)  voluntarily disclosed the PIN and banking credentials such as access identity (ID) and passcode to a third party; (iv)  recorded the PIN on the Card or on anything kept in close proximity with the Card; (v) left the Card or an item containing the Card unattended in places visible and accessible to others; or (vi)  voluntarily allowed another person to use the Card and the Cardholder has taken reasonable steps to keep the Cardholder's security device secure at all times as well as has cooperated with the Bank in the investigation."
      },
      "doc2": {
        "content": "Pemegang Kad tidak akan dipertanggungjawab ke atas urus niaga tanpa kebenaran kad-hadir yang memerlukan pengesahan PIN atau tandatangan yang telah disahkan atau penggunaan kad tanpa-sentuh, dengan syarat Pemegang Kad tidak: 8.6.1  melakukan penipuan; 8.6.2  tangguh  dalam  memaklum  Bank  secepat  mungkin  setelah  diketahui  kehilangan  atau penggunaan tanpa kebenaran Kad Kredit; 8.6.3  secara sukarela mendedahkan PIN kepada orang lain; 8.6.4  mencatatkan PIN pada Kad Kredit atau pada apa-apa yang disimpan berdekatan dengan Kad; 8.6.5  meninggalkan Kad Kredit atau apa-apa yang mengandungi Kad Kredit tanpa jagaan di manamana tempat yang boleh dilihat dan diakses oleh orang lain; atau 8.6.6  secara sukarela membenarkan orang lain untuk menggunakan Kad."
      },
      "discrepancies": [
        "1. 'Kad Kredit' is used instead of 'Kad Debit' in several places (language mixing/incorrect term).",
        "2. 'banking credentials such as access identity (ID) and passcode' is omitted in BM version.",
        "3. 'the Cardholder has taken reasonable steps to keep the Cardholder's security device secure at all times as well as has cooperated with the Bank in the investigation' is omitted in BM version."
      ],
      "explanation": "BM version uses 'Kad Kredit' instead of 'Kad Debit', omits 'banking credentials' and the clause about security device and cooperation."
    },
    {
      "location": "Section 9.0, Clause 9.1",
      "doc1": {
        "content": "The Cardholder may at any time terminate the use of the Debit Card by written notice to the Bank and returning the Debit Card cut in half to the Bank. No refund of the Fee or any part thereof will be made to the Cardholder and the Cardholder shall be and remain liable for any transaction effected through the use of the Debit Card prior to termination of the Cardholder's Debit Card."
      },
      "doc2": {
        "content": "Pemegang  Kad  boleh  pada  bila-bila  masa,  menamatkan  penggunaan  Kad  Debit  dengan memberikan makluman bertulis kepada Bank dan mengembalikan Kad Debit yang dipotong dua kepada Bank. Tiada kembalian Fi atau sebahagiannya akan dibuat kepada Pemegang Kad dan Pemegang Kad akan dan kekal bertanggungjawab ke atas sebarang transaksi yang dilakukan menggunakan Kad Debit sebelum Bank menerima makluman bertulis mengenai penamatan dan pengembalian Kad Debit dipotong dua kepada Bank."
      },
      "discrepancies": [
        "1. 'prior to termination of the Cardholder's Debit Card' is translated as 'sebelum Bank menerima makluman bertulis mengenai penamatan dan pengembalian Kad Debit dipotong dua kepada Bank', which adds a requirement for written notice and return of card, not present in English."
      ],
      "explanation": "BM version adds a requirement for written notice and return of card for termination."
    },
    {
      "location": "Section 10.0, Clause 10.2",
      "doc1": {
        "content": "The following Fees, commissions and/or charges is imposed at the following rate or such other rate as the Bank shall at its discretion vary from time to time by giving twenty-one (21) calendar days' prior notice to the Cardholder for transactions effected by use of the Debit Card. For the full list of fees and charges, please visit our website www.hlb.com.my/dc1 or scan here:"
      },
      "doc2": {
        "content": "Bayaran, komisen dan/atau caj berikut dikenakan pada kadar yang dinyatakan atau kadar lain yang ditetapkan, yang boleh dipinda oleh Bank untuk membuat pemindahan dari semasa ke semasa dengan memberi dua puluh satu (21) hari kalendar notis terlebih dahulu kepada Pemegang Kad untuk transaksi yang dilaksanakan melalui penggunaan Kad Debit. Untuk senarai fi dan caj yang lengkap, sila layari laman web kami www.hlb.com.my/dc2 atau imbas di sini:"
      },
      "discrepancies": [
        "1. English version uses 'www.hlb.com.my/dc1', BM version uses 'www.hlb.com.my/dc2' (different website links)."
      ],
      "explanation": "BM version uses a different website link for fees and charges."
    },
    {
      "location": "Section 10.0, Clause 10.3",
      "doc1": {
        "content": "The Annual Fee is not chargeable on the issuance of the Debit Card and it will only be charged on the anniversary date. The Annual Fee may be varied by the Bank from time to time with twenty-one (21) calendar days' prior notice via the Bank's Websites or in other manner the Bank deems fit."
      },
      "doc2": {
        "content": "Fi Tahunan tidak akan dikenakan semasa pengeluaran Kad Debit dan hanya akan dikenakan pada tarikh ulang tahun. Fi Tahunan boleh diubah oleh Bank dari semasa ke semasa. Fi Tahunan tidak akan dikembalikan."
      },
      "discrepancies": [
        "1. 'with twenty-one (21) calendar days' prior notice via the Bank's Websites or in other manner the Bank deems fit' is omitted in BM version.",
        "2. 'Fi Tahunan tidak akan dikembalikan.' (Annual Fee will not be refunded) is added in BM version, not present in English."
      ],
      "explanation": "BM version omits the notice requirement and adds a non-refundability clause."
    },
    {
      "location": "Section 12.0, Clause 12.4",
      "doc1": {
        "content": "The Daily Online Purchase Limit for Generic and Priority Banking Cardholder is defaulted at Ringgit Malaysia  One  Thousand  (RM1,000),  with  a  maximum  allowable  limit  of  Ringgit  Malaysia  Twenty Thousand (RM20,000) for Generic and Priority Banking Cardholders, or such other limit determined by the Bank from time to time by giving twenty-one (21) calendar days' prior notice to the Cardholder. The Cardholder can perform the Daily Online Purchase Limit setting at any branches of the Bank or via Hong Leong Connect. In addition, with effect from 24 September 2022, the Cardholder can apply for a higher Daily Online Purchase Limit (' Temporary Daily Online Purchase Limit ') via Hong Leong Connect and such Temporary Daily Online Purchase Limit shall be valid within a specific time frame selected by the Cardholder (' Date Range '),  The Temporary Daily Online Purchase Limit gives the Cardholder a maximum allowable limit of Ringgit Malaysia Thirty Thousand (RM30,000) during the Date Range. The Temporary Daily Online Purchase Limit will cease upon the expiry of the Date Range and thereafter the Online Purchase Limit will revert to the Daily Online Purchase Limit."
      },
      "doc2": {
        "content": "Had  Belian  Dalam  Talian  Harian  untuk  Pemegang  Kad  Biasa  dan  Pemegang  Kad  Perbankan Prioriti ditetapkan pada Ringgit Malaysia Satu Ribu (RM1,000), dengan had maksimum dibenarkan sebanyak  Ringgit  Malaysia  Dua  Puluh  Ribu  (RM20,000)  untuk  Pemegang  Kad  Biasa  dan Pemegang Kad Perbankan Prioriti, atau suatu amaun lain yang ditentukan oleh Bank dari semasa ke semasa dengan memberikan notis awal dua puluh satu (21) hari kalendar kepada Pemegang Kad. Pemegang Kad boleh melakukan Had Belian Dalam Talian Harian di mana-mana cawangan Bank atau melalui Hong Leong Connect. Selain daripada itu, berkuat kuasa 24 September 2022, Pemegang Kad boleh memohon Had Belian Dalam Talian Harian yang lebih tinggi (' Had Belian Dalam Talian Harian Sementara ') melalui Hong Leong Connect dan Had Belian Dalam Talian Seharian Sementara tersebut akan berkuat kuasa sepanjang tempoh masa tertentu yang dipilih oleh Pemegang Kad (' Julat Tarikh '). Had Belian Dalam Talian Harian Sementara memberikan Pemegang  Kad  had  maksimum  yang  dibenarkan  iaitu  Ringgit  Malaysia  Tiga  Puluh  Ribu (RM30,000) semasa Julat Tarikh. Had Belian Dalam Talian Harian Sementara akan ditamatkan apabila Julat Tarikh berakhir dan selepas itu, Had Belian Runcit akan Kembali kepada Had BelianDalam Talian Harian."
      },
      "discrepancies": [
        "1. 'Had Belian Dalam Talian Seharian Sementara' is a spelling/word error; should be 'Had Belian Dalam Talian Harian Sementara'.",
        "2. 'Had Belian Runcit akan Kembali kepada Had BelianDalam Talian Harian' is a word error; should be 'Had Belian Dalam Talian Harian'."
      ],
      "explanation": "BM version contains a spelling/word error and a word concatenation error."
    },
    {
      "location": "Section 13.0, Clause 13.1",
      "doc1": {
        "content": "The Debit Card shall not be used at any merchants who are in the business of providing non-Shariah compliant Goods and Services and/or for any non-Shariah compliant transactions categorized by the following Merchant Category as per below: (i) Bars, Cocktail Lounges, Discotheque, Nightclubs and Taverns (ii) Packages Beer, Wine and Liquor (iii) Cigar Stores and Stands (iv) Gambling Transactions (v) Gambling-Horse Racing, Dog Racing, Non-Sports Intrastate Internet Gambling (vi) Dating and Escort Services"
      },
      "doc2": {
        "content": "Kad Debit tidak boleh digunakan di  mana-mana  peniaga  runcit  yang menyediakan barang dan perkhidmatan yang tidak mematuhi Syariah dan/atau untuk apa-apa transaksi yang tidak mematuhi Syariah yang dikategorikan mengikut Kategori peniaga seperti yang berikut: (i) Bar, Ruang Koktel, Disko, Kelab Malam dan Kedai Minuman Keras (ii) Pakej Bir, Wain dan Minuman Keras (iii)  Kedai dan gerai cerut (iv)  Tranksaksi Perjudian (v) Petaruhan-Perlumbaan  Kuda,  Perlumbaan  Anjing,  Petaruhan  Bukan  Sukan  Dalam  Talian Antara Negeri (vi)  Perkhidmatan Janji Temu dan Teman Social"
      },
      "discrepancies": [
        "1. 'Dating and Escort Services' is translated as 'Perkhidmatan Janji Temu dan Teman Social', which adds 'Teman Social' (Social Companion), not present in English.",
        "2. 'Cigar Stores and Stands' is translated as 'Kedai dan gerai cerut' (acceptable).",
        "3. 'Gambling Transactions' is translated as 'Tranksaksi Perjudian', which contains a spelling error; should be 'Transaksi Perjudian'."
      ],
      "explanation": "BM version adds 'Teman Social' and contains a spelling error."
    },
    {
      "location": "Section 15.0, Clause 15.1",
      "doc1": {
        "content": "The Bank reserves the right to withdraw or suspend at its discretion the Debit Card and/or any of the Services and in such circumstances if the Bank so deems fit to terminate use of the Debit Card by the Cardholder with written notice to the Cardholder. It is further agreed that the Bank is under no obligation whatsoever to reveal the reason for the termination of use of the Debit Card."
      },
      "doc2": {
        "content": "Bank berhak menarik atau menggantung mengikut budi bicaranya Kad Debit dan/atau mana-mana Perkhidmatan  dan  dalam  keadaan  seperti  itu  jika  Bank  dianggap  sesuai  untuk  menghentikan penggunaan Kad Debit oleh Pemegang Kad dengan pemberitahuan bertulis kepada Pemegang Kad. Selanjutnya disepakati bahawa  Bank  tidak  berkewajiban untuk menyatakan  alasan penamatan penggunaan Kad Debit."
      },
      "discrepancies": [
        "1. 'no obligation whatsoever to reveal the reason' is translated as 'tidak berkewajiban untuk menyatakan alasan', omitting 'whatsoever'."
      ],
      "explanation": "BM version omits 'whatsoever' in the obligation clause."
    },
    {
      "location": "Section 16.0, Clause 16.2",
      "doc1": {
        "content": "The Bank is entitled at its discretion to: (a) suspend the Cardholder's right to use the Debit Card entirely or in respect of specified privileges. (b) refuse to re-issue, renew or replace the Debit Card, without in any case, affecting the obligations of the Cardholder under these T&amp;Cs which will continue in force, and there will be no refund of any Annual Fee or other fees paid if the right to use the Debit Card is suspended by the Bank or if the Debit Card is not renewed or replaced."
      },
      "doc2": {
        "content": "(a) Menggantung  hak  Pemegang  Kad  untuk  menggunakan  Kad  Debit  sepenuhnya  atau berkenaan keistimewaan tertentu. (b) Menolak untuk menerbit-semula, memperbaharui atau mengganti Kad Debit, tanpa dalam apa jua perkara, menjejaskan tanggungjawab Pemegang Kad di bawah T&amp;S ini yang akan terus berkuatkuasa dan tiada pengembalian akan dibuat untuk sebarang fi tahunan atau fi lain yang telah dibayar jika hak untuk menggunakan Kad Debit digantung oleh Bank atau jika Kad Debit tidak diperbaharui atau diganti."
      },
      "discrepancies": [
        "1. 're-issue' is translated as 'menerbit-semula', which is a spelling error; should be 'menerbit semula'."
      ],
      "explanation": "BM version contains a spelling error: 'menerbit-semula'."
    },
    {
      "location": "Section 19.0, Clause 19.3",
      "doc1": {
        "content": "In the event the Bank extends the time period for the completion of an investigation beyond fourteen (14) calendar days from the date a disputed Card Transaction is first reported, whether orally or in writing, by Cardholder to the Bank, the Bank must: (a) at a minimum, provisionally credit the full amount of the disputed transaction or Ringgit Malaysia Five Thousand (RM5,000), whichever is lower (including any interest or profit where applicable), into the Retail Purchase Account no later than fourteen (14) calendar days from the date the Cardholder provides the Bank with the information set out under Clause19.2 herein; (b) credit the remaining amount of the disputed Card Transaction (including any interest or profit where applicable) no later than thirty (30) calendar days from the date of the first crediting where the Bank has provisionally credited an amount into the Retail Purchase Account in accordance with Clause 19.3(a) herein which is lesser than the amount of the disputed Card Transaction; and (c) allow the Cardholder the full use of the provisionally credited funds."
      },
      "doc2": {
        "content": "Bank boleh:  sekurang-kurangnya, sementara mengkreditkan jumlah penuh transaksi yang dipertikaikan atau Ringgit Malaysia Lima Ribu (RM5,000), yang mana lebih rendah (termasuk apa-apa keuntungan yang berkenaan), ke dalam Akaun Pembelian Runcit tidak lewat daripada empat belas (14) hari kalendar dari tarikh Pemegang Kad mengemukakan maklumat yang dinyatakandalam Klausa 19.2 kepada Bank; (a) mengkredit  baki  Transaksi  Kad  yang  dipertikaikan  (termasuk  apa-apa  keuntungan  yang berkenaan) tidak  lewat  daripada tiga  puluh  (30) hari  kalendar  daripada  tarikh  perkreditan pertama dana sementara ke dalam Akaun Pembelian Runcit oleh Bank mengikut Klausa 19.3 (a)  di mana dana tersebut adalah kurang daripada amaun Transaksi Kad yang dipertikaikan; dan (b) membenarkan Pemegang Kad menggunakan sepenuhnya dana sementara yang dikreditkan."
      },
      "discrepancies": [
        "1. 'the Bank must' is translated as 'Bank boleh', which changes the obligation to an option.",
        "2. 'allow the Cardholder the full use of the provisionally credited funds' is translated as 'membenarkan Pemegang Kad menggunakan sepenuhnya dana sementara yang dikreditkan' (acceptable)."
      ],
      "explanation": "BM version changes 'must' to 'boleh', changing the obligation to an option."
    },
    {
      "location": "Section 19.0, Clause 19.7",
      "doc1": {
        "content": "Subject to the Cardholder's compliance with its obligations under Clause 19.2, in the event of any chargeback  due  to  a  complaint  or  dispute  raised  by  the  Cardholder  pertaining  to  Overseas Transactions (as defined under Clause 20.1 below) transacted in foreign currency through the MCF Enabled Account, the amount of chargeback shall be credited into the Cardholder's MCF enabled Account in the currency of the original transaction."
      },
      "doc2": {
        "content": "Tertakluk  kepada  kepatuhan  Pemegang  Kad  kepada  tanggungjawab  yang  dinyatakan  dalam Klausa  19.2,  sekiranya  berlaku  caj  balik  akibat  aduan  atau  pertikaian  oleh  Pemegang  Kad mengenai Transaksi Luar Negara (seperti yang ditakrifkan di bawah Klausa 19.1 di bawah) yang dilakukan dalam mata wang asing melalui Akaun Yang Diupayakan Dengan MCF, amaun yang dicaj balik akan dikreditkan ke dalam Akaun Yang Diupayakan Dengan MCF Pemegang Kad dalam mata wang transaksi asal."
      },
      "discrepancies": [
        "1. 'Clause 20.1 below' is translated as 'Klausa 19.1 di bawah', which is a clause numbering error."
      ],
      "explanation": "BM version references the wrong clause number."
    },
    {
      "location": "Section 20.0, Clause 20.1",
      "doc1": {
        "content": "The Cardholder may use the Debit Card to perform Card Transaction(s) and ATM Card Transactions outside Malaysia (' Overseas Transactions ') where there are Authorised Merchant and/or Authorised Cash Outlets provided that the Cardholder has opted to allow Overseas Transactions to be performed on the relevant Debit Card in accordance with Clause 20.1 herein."
      },
      "doc2": {
        "content": "Kad ATM di luar Malaysia ('Transaksi Luar Negara') di mana terdapat  Peniaga Sah dan/atau Saluaran  Tunai  yang  dibenarkan  dengan  syarat  bahawa  Pemegang  Kad  telah  memilih  untuk membenarkan Transaksi Luar Negara yang akan dilaksanakan pada Kad Debit yang berkaitan Klausa 20.1 di dalam ini."
      },
      "discrepancies": [
        "1. 'The Cardholder may use the Debit Card to perform Card Transaction(s) and ATM Card Transactions outside Malaysia' is omitted in BM version.",
        "2. 'Authorised Cash Outlets' is translated as 'Saluaran Tunai yang dibenarkan', which is a spelling error; should be 'Saluran Tunai'."
      ],
      "explanation": "BM version omits the opening phrase and contains a spelling error."
    },
    {
      "location": "Section 20.0, Clause 20.6(i)",
      "doc1": {
        "content": "the  foreign  exchange  rate  used  by  the  merchant  may  be  higher  than  the  exchange  rate determined by Visa or Mastercard;"
      },
      "doc2": {
        "content": "Kadar pertukaran asing yang digunakan oleh peniaga luar negara bagi urusniaga DCCmungkin lebih tinggi daripada kadar pertukaran yang ditentukan oleh Visa atau Mastercard."
      },
      "discrepancies": [
        "1. 'DCCmungkin' is a word concatenation error; should be 'DCC mungkin'."
      ],
      "explanation": "BM version contains a word concatenation error."
    },
    {
      "location": "Section 22.0, Clause 22.2",
      "doc1": {
        "content": "The Cardholder is not allowed to request the Authorised Merchant to change its chosen debit card network."
      },
      "doc2": {
        "content": "Pemegang Kad tidak dibenarkan untuk meminta Peniaga Sah yang dibenarkan untuk menukar rangkaian Kad Debit yang telah dipilih."
      },
      "discrepancies": [
        "1. 'Authorised Merchant' is translated as 'Peniaga Sah yang dibenarkan', which is redundant as 'Peniaga Sah' already means 'Authorised Merchant'."
      ],
      "explanation": "BM version redundantly translates 'Authorised Merchant'."
    },
    {
      "location": "Section 24.0, Final Contact Information",
      "doc1": {
        "content": "If you have any enquiries regarding these T&amp;Cs, you may seek clarification from our staff who attended to you. Alternatively, please email us at hlonline@hlbb.hongleong.com.my or call 03-7626 8899."
      },
      "doc2": {
        "content": "Jika  anda  mempunyai  sebarang  pertanyaan  mengenai  T&amp;S  ini,  anda  boleh  mendapatkan  penjelasan daripada  kakitangan  kami  yang  membantu  anda.  Sebagai  alternatif,  sila  e-mel  kepada  kami  di hlonine@hlbb.hongleong.com.my atau hubungi 03-7626 8899"
      },
      "discrepancies": [
        "1. 'hlonline@hlbb.hongleong.com.my' is misspelled as 'hlonine@hlbb.hongleong.com.my' in BM version.",
        "2. Missing period at the end of the BM sentence."
      ],
      "explanation": "BM version contains an email address spelling error and omits the period at the end."
    }
  ]
}
```
"""
json_str = result
match = re.search(r"```json\s*(\{.*\})\s*```", result, re.DOTALL)
result_dict = {}
if match:
    json_str = match.group(1)
    json_str = re.sub(r"}\s*//.*?(?=\s*\]\s*})", "}", json_str, re.DOTALL)
try:
    result_dict = json.loads(json_str)  # Attempt to parse the JSON
    # if result_dict.get("flags"):  # Check if "flags" key exists and is not empty
    #     print(json.dumps(result_dict, indent=2))
    # else:
    #     print("No flags found in the result.")
except json.JSONDecodeError as e:
    print(e)

print(result_dict)
