# Dala va mavsum qoidalari

> Foydalanuvchi uchun ishlatish yo'riqnomasi: [QOLLANMA.md](QOLLANMA.md) (`1_TAYYORLASH.bat` → qo'lda tuzatish → `2_EKSPORT.bat`).

Loyiha: ekin yerlarining suv iste'molini aniqlash uchun to'liq dala va to'g'ri mavsum.
Manba: `boshqalar/boshqalar.shp` (502 356 poligon, 2026). Natija: `natija/ekin_yerlar_v1.gpkg`.

## 1. `ekin_davri` ning ma'nosi (qishloq xo'jaligi shevasi)

| `ekin_davri` (asl) | `mavsum` (yangi) | Ma'nosi |
|---|---|---|
| Bahorgi | Birlamchi ekin | yilning 1-ekini |
| Kuzgi | Ikkilamchi ekin | birlamchidan keyingi (takroriy) ekin |
| Mavsumiy | Mavsumiy ekin | butun yil shu ekin turadi |

## 2. `turi` bo'yicha qoidalar (`ekin_davri` bo'sh bo'lganlar uchun)

| turi | mavsum | izoh |
|---|---|---|
| Bug'doy | Birlamchi ekin | |
| Ozuqa | Birlamchi ekin | paxtadan oldin mart–aprelda ekiladi |
| Paxta | Mavsumiy ekin | |
| Bog' | Mavsumiy ekin | |
| Boshqa | Mavsumiy ekin | turi aniqlanmagan ekin; hech qaysi ekin bilan ustma-ust tushmaydi (tekshirildi) |
| Ikkilamchi ekin aniqlanmagan | Ikkilamchi ekin | ekilgan, lekin turi aniqlanmagan (jamoa qo'shgan) |
| Baliqxovuz, Issiqxona | bo'sh | ekin emas, tegilmaydi |

## 3. Qatlamlar va to'liq dala

- Qatlamlarning ustma-ust turishi **to'g'ri**: bir joyda Birlamchi, uning ustida Ikkilamchi bo'ladi.
- Alohida to'liq dala konturi yo'q, lekin fayldagi barcha poligonlar birgalikda dalani to'liq qoplaydi. Muammo faqat mavsumlar bo'yicha bo'linishda.
- Har bir to'liq dala **har mavsumda to'liq tushuntirilishi** kerak:
  - Ikkilamchi ekin butun dalaga ekilsa, kuzgi mavsum to'liq dala bo'ladi.
  - Ikki mavsumda ham ekilmagan qism **Mavsumiy** ga o'tadi.
- **Ozuqa (yoki Bug'doy) ustida Paxta** bo'lsa, Paxta ikkinchi mavsumni **yopgan** hisoblanadi. Bunday joyga "Ikkilamchi ekin aniqlanmagan" qo'yilmaydi.
- Birlamchidan keyin Paxta ekilgan joyda **ikkilamchi bo'lmaydi**. Agar u yerda allaqachon Ikkilamchi kontur turgan bo'lsa
  (asosan jamoa qo'shgan "Ikkilamchi ekin aniqlanmagan"), uning **Paxta (Mavsumiy) ustidagi qismi kesiladi**;
  qolgan qismi haqiqiy bo'lmasa (< 0.02 ga yoki eni < 6 m) kontur butunlay olib tashlanadi. Kesilgan/olib tashlangan
  qismlar `tashlangan` qatlamiga `sabab` bilan yoziladi; kesilgan asl kontur `kesildi = 1`.

## 4. Balans qoidasi

Soni teng bo'lishi shart emas: bitta birlamchi ustida bir nechta ikkilamchi bo'lak bo'lishi mumkin, teskarisi ham.
Tekshiruv **maydon** bo'yicha qilinadi:

```
Birlamchi − Ikkilamchi = (Mavsumiy bilan yopilgan, Ikkilamchisiz Birlamchi) − (Mavsumiy ustidagi, Birlamchisiz Ikkilamchi)
```
Ya'ni: har bir joyda Birlamchi bor bo'lsa, ustida Ikkilamchi yoki Mavsumiy bor; Ikkilamchi bor bo'lsa, ostida
Birlamchi yoki Mavsumiy bor. Mavsumiy (masalan Paxta, Boshqa) ikkala mavsumni ham yopadi.

Yetimlarni to'ldirish:
- ostida Birlamchi yo'q Ikkilamchi → ostiga **"Birlamchi ekin aniqlanmagan"**
- ustida Ikkilamchi ham, Mavsumiy ham yo'q Birlamchi → ustiga **"Ikkilamchi ekin aniqlanmagan"**

Yangi bo'lak geometriyasi:
- Manba ustida/ostida boshqa mavsum umuman yo'q → yangi bo'lak manbaning **aynan nusxasi** (asl koordinatalar, `aniq_nusxa = 1`).
- Manba qisman yopilgan → yangi bo'lak = manba **minus** yopuvchi poligonlar (aniq ayirma, `aniq_nusxa = 0`).
- Burchaklar yumaloqlanmaydi, geometriya buffer bilan o'zgartirilmaydi.
- Ayirmadan faqat chiziq xatosi qolsa (barcha qismlari < 0.02 ga yoki eni < 6 m) → yangi bo'lak yaratilmaydi, qoldiq `tashlangan` qatlamiga yoziladi.

Yangi bo'lak ustunlari:
- `manba_turi` — yangi bo'lak qaysi poligondan olingan (masalan Kartoshka = ostiga Birlamchi qo'shilgan Ikkilamchi).
- `qoshni_turi` — 5 m ichida tegib turgan eng katta shu mavsumdagi ekin; **faqat taklif**.
- **Qaror:** `qoshni_turi = Bug'doy` bo'lsa ham `turi` hozircha **"Birlamchi ekin aniqlanmagan"** qoladi
  (ekin turini aniqlash ish doirasiga kirmaydi — 8-bo'lim).
- `dala_id` — faqat ustma-ust tushgan bo'laklar guruhi; yonma-yon bo'laklar birlashtirilmaydi (qaror, 8-bo'lim).

## 5. Texnik

- Maydon uchun `maydon` ustuni ishlatiladi (haqiqiy ga). `Shape_Area` va `st_area_sh` Web Mercatorda hisoblangan, ~1.69 marta katta, ishlatilmaydi.
- Apostroflar `'` ga keltirildi; buzuq geometriyalar `make_valid` bilan tuzatildi (`geom_tuzatildi = 1`).
- `crop_id` keyinroq to'g'rilanadi ("Ikkilamchi ekin aniqlanmagan" da 25 va 6 aralash).
- Ma'lumot faqat lokal PC da qoladi.

## 6. Qilingan ishlar

### 2026-11-04 — Diagnostika (asl shp, o'zgartirilmagan)
- 502 356 poligon, 4 viloyat, `yil` = 2026, EPSG:3857.
- Bug'doy kuzgi qatlam bilan (kuzgi ekinlar + "Ikkilamchi ekin aniqlanmagan") ~100% yopilgan (qoldiq 173 ga).
- Yetim holatlar: ostida Birlamchi yo'q Ikkilamchi 83.4 ming ga (asosan Makka 59.7 ming); ustida Ikkilamchi yo'q Birlamchi 27.1 ming ga
  (shundan 6.8 ming ga — ustida Paxta turgan Ozuqa/Bug'doy, tabiiy holat).
- "Boshqa" hech qaysi ekin bilan ustma-ust tushmaydi (49 joyda jami 103 m² chiziq xatosi) → Mavsumiy.
- Birlamchi va Ikkilamchi soni teng bo'lmasligi normal (bitta birlamchi ustida 2–5 ikkilamchi bo'lak bo'lishi mumkin); balans maydon bo'yicha.

### 2026-11-04 — 1-bosqich: atributlar → `natija/ekin_yerlar_v1.gpkg`
Skriptlar: `scripts/01_atribut_mavsum.py`, `01b_tekshirish.py`, `01c_boshqa_mavsumiy.py`
- 502 356 qatorning hammasi ko'chirildi; `fid_asl` = asl shp FID.
- Apostroflar `'` ga keltirildi (`turi`, `vh`, `tuman`, `f_name`).
- 213 ta buzuq geometriya tuzatildi (`geom_tuzatildi = 1`); invalid qolmadi.
- `mavsum` ustuni: Birlamchi 88 970 (520 ming ga), Ikkilamchi 108 599 (576 ming ga), Mavsumiy 297 653 (1 184 ming ga),
  bo'sh 7 134 (Baliqxovuz, Issiqxona).

### 2026-11-04 — 2–3 bosqich sinovi: Jomboy tumani → `natija/sinov_jomboy_v2.gpkg`
Skriptlar: `scripts/02_dala_toldirish.py`, `02b_tekshirish.py`, `02c_teshik_tekshirish.py`
- Qo'shildi: 1 803 ta "Birlamchi ekin aniqlanmagan", 686 ta "Ikkilamchi ekin aniqlanmagan"
  (2 411 tasi manbaning aynan nusxasi, 78 tasi aniq ayirma).
- Balans: Birlamchi 11 213 → **16 599 ga**, Ikkilamchi 15 493 → **16 599 ga**, farq 0.
- Mavsum qatlamlarida teshik: Birlamchi jami 9 m², Ikkilamchi 2.6 m² (asl chiziq nomuvofiqligi).
- Asl qatorlar va geometriya o'zgarmaganligi tekshirildi.
- `sinov_jomboy.gpkg` (v1) — **xato versiya**: buffer burchaklarni yumaloqlagan (~2.4 ga ochiq joy); ishlatilmaydi.

### 2026-11-04 — Jomboy v3: atributlar → `natija/sinov_jomboy_v3.gpkg` (amaldagi versiya)
- Ko'p qismli yangi bo'laklar ajratildi: 2 489 yozuv → 2 490 alohida bo'lak (Jomboyda faqat 1 ta ko'p qismli bor edi);
  endi har bir yangi qator bitta Polygon.
- Fermer ma'lumoti katta daladan o'tkazildi: **1 742 ta asl ikkilamchi** poligonga (Loviya 1 646, Makka 70, Mosh 25,
  Beda 1; jami ~6 880 ga). Mavjud qiymat birortasi ham almashtirilmadi. `fermer_aralash = 1`: 11 ta.
- Jamoa qo'shgan 949 ta "Ikkilamchi ekin aniqlanmagan" da `crop_id`, `vh`, `yld` tozalandi; fermer ma'lumoti saqlandi.
- "aniqlanmagan" turlarda `crop_id` bo'sh.
- Fermer ma'lumoti bo'sh qolganlar — ostida/ustida fermerli poligon yo'q joylar (ma'lumot asl faylda ham yo'q):
  asl Birlamchi 1 021 (2 271 ga), asl Ikkilamchi 2 159 (6 548 ga), Mavsumiy 4 800 (12 311 ga), yangi bo'laklar 2 490 (6 492 ga).
- Balans, teshik va aniq nusxa tekshiruvlari v2 bilan bir xil (farq 0, teshik 9 m² / 2.6 m², 2 411/2 411 aniq).

### 2026-11-04 — Jomboy v4: yakuniy format → `natija/sinov_jomboy_v4.gpkg`
- 3 qatlam: `ekin_yerlar` (asl 12 766 + yangi 2 489), `qoshilgan` (2 489), `tashlangan` (1 114). `dala` qatlami olib tashlandi
  (`dala_id` ustuni qoladi).
- Barcha 22 asl ustun saqlandi; `Shape_*`/`st_*` ustunlari geodezik maydon (m²) va perimetr (m) bilan qayta hisoblandi.
- Tuman chegarasi uchun kontekst: Jomboy atrofidan 356 ta qo'shni poligon hisobga olindi.
- Ajratilgandan keyin chiziq xatosi bo'lib qolgan 1 ta mayda qism (~0 m²) yangi bo'lak qilinmadi, `tashlangan` ga o'tdi.
- Tekshiruvlar: ruxsat etilmagan o'zgarish yo'q, mavjud fermer qiymati almashtirilmagan, yangi bo'laklar bitta Polygon,
  balans farqi 0, teshik 9 m² / 2.6 m².

### 2026-11-04 — YAKUNIY NATIJA: barcha 70 tuman → `natija/ekin_yerlar_yakuniy.gpkg`
Skriptlar: `02_dala_toldirish.py --hammasi`, `03_yakuniy_tekshirish.py`, `04_xatolar_excel.py`
Jurnal: `natija/yakuniy_log.txt`, tekshiruv: `natija/yakuniy_tekshiruv.txt`, tuman balansi: `natija/ekin_yerlar_yakuniy_tuman_balans.csv`,
xatolar: `natija/xatolar_hisoboti.xlsx`

| | Qiymat |
|---|---|
| `ekin_yerlar` | 539 643 (asl 502 353 + yangi 37 290) |
| `qoshilgan` | 37 290 |
| `tashlangan` | 14 831 (Paxta ustidan kesilgan/olib tashlangan + chiziq xatolari) |
| Paxta ustidagi Ikkilamchi | 11 kontur kesildi, 3 kontur olib tashlandi (~186 ga, 11 tumanda) |
| Birlamchi / Ikkilamchi | 603 499 ga / 596 522 ga; farq = Mavsumiy (Paxta) bilan yopilgan Birlamchi 6 973 ga; qoldiq farq 1.7 ga |
| Fermer ma'lumoti o'tkazildi | 28 788 asl poligonga; fermer_aralash 385 |
| `maydon` qayta hisoblandi | > 1% farqlisi 296 ta |

Tekshiruv natijasi (4 viloyat): barcha asl `fid_asl` bor (3 olib tashlangandan tashqari), kesilmagan asl geometriya
koordinatama-koordinata bir xil, ruxsatsiz atribut o'zgarishi 0, invalid geometriya 0, yangi bo'laklarning hammasi bitta Polygon,
"aniqlanmagan" larda `crop_id` bo'sh, `maydon` va `Shape_Area` haqiqiy maydon bilan mos (yaxlitlash darajasida).
Tuman ichidagi balans farqi va "teshik" faqat 4 juft tuman chegarasida (Guliston/Guliston shahri, Shahrisabz/Shahrisabz shahri,
Samarqand shahri/Oqdaryo, Yozyovon/Oltiariq) — juftlarni birga hisoblaganda haqiqiy teshik 0.

Tezlashtirish (parallel, 14 jarayon): `02` ~20 daq → **3.4 daq**, `03` ~15 daq → **7 daq**, `04` ~5 daq → **0.5 daq**
(jami ~45 daq → ~11 daq). Parallel natija ketma-ket natija bilan uch qatlamda ham atribut va geometriya bo'yicha **aynan bir xil**.
`02` ichidagi takroriy balans tekshiruvi endi ixtiyoriy (`--ichki-tekshiruv`), chunki `03` buni to'liq qiladi.

Yo'lda topilib tuzatilgan texnik xatolar: yangi bo'laksiz tuman (Dehqonobod) da to'xtash; proyeksiyadan keyin GEOS topologiya
xatosi (1 sm aniqlikda qayta urinish); 3857 ga qaytarilganda o'z-o'zini kesgan 20 ta yangi bo'lak (tuzatiladi).

## 7. Qanday qilindi (usul)

Hamma hisob lokal PC da, `gis_pro` conda muhitida (Python: geopandas, shapely 2, pyogrio, scipy).
Maydon va masofa hisoblari teng maydonli proyeksiyada qilinadi:
`+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=67` (Albers, metr). Natija fayllar asl EPSG:3857 da yoziladi.

### 7.1 Diagnostika: ustma-ustlikni topish
1. Har bir viloyat alohida o'qildi va Albers ga o'tkazildi; buzuq geometriyalar vaqtincha `make_valid` qilindi.
2. Fazoviy indeks (STRtree) bilan har bir poligonga tegib turgan barcha poligonlar topildi.
3. Har bir juft uchun kesishma maydoni hisoblandi. **1 m² dan katta** kesishma = ustma-ust tushish;
   undan kichigi chegarada tegib turish yoki chiziq xatosi deb olindi.
4. Juftlar `turi` × `ekin_davri` bo'yicha guruhlanib, kim kimning ustida turgani va har bir poligonning necha foizi
   boshqa mavsum bilan yopilgani hisoblandi.
5. Yetim poligonlar uchun 5 m ichidagi qo'shnilar tekshirildi: yetim bo'laklar boshqa mavsum poligonining
   siljigan nusxasi emas, alohida yerlar ekani shu yo'l bilan aniqlandi.
6. `maydon` ustuni Albers maydoni bilan solishtirildi (nisbat 1.0000); `Shape_Area` ~1.69 marta katta (Mercator).

### 7.2 1-bosqich: atributlar (`01_atribut_mavsum.py`)
1. Shp viloyatma-viloyat o'qiladi (xotira uchun), asl FID `fid_asl` ga yoziladi.
2. Barcha matn ustunlarida `‘ ’ ʻ ʼ ` ´` belgilari `'` ga almashtiriladi.
3. `is_valid` bo'lmagan geometriya `make_valid` qilinadi; natijadan faqat Polygon/MultiPolygon qismlari olinadi.
4. `mavsum` 2-bo'limdagi jadval bo'yicha to'ldiriladi: avval `turi` qoidasi, bo'lmasa `ekin_davri` qoidasi.
5. Natija GeoPackage ga yoziladi (shapefile dbf 2 GB chegarasiga sig'maydi). `01b_tekshirish.py` soni, validlik,
   apostrof va mavsum jadvalini tekshiradi.

### 7.3 2–3 bosqich: yetimlarni to'ldirish (`02_dala_toldirish.py`)
Har bir tuman alohida ishlanadi.
1. Har poligonga sinf beriladi: B (Birlamchi), I (Ikkilamchi), M (Mavsumiy), `-` (Baliqxovuz, Issiqxona).
2. **Ostiga Birlamchi kerakmi?** Har bir I poligon uchun STRtree bilan unga tegib turgan B va M poligonlar olinadi:
   - hech biri yo'q (yoki faqat chegarada tegadi) → yangi "Birlamchi ekin aniqlanmagan" = I ning **aynan nusxasi**;
   - bor → qoldiq = I **minus** (B ∪ M). Qoldiqning birorta qismi haqiqiy bo'lsa (≥ 0.02 ga va 3 m ichkariga
     qisqartirganda yo'qolib ketmasa, ya'ni eni ≥ 6 m), butun qoldiq **o'zgarishsiz** yangi bo'lak bo'ladi;
     aks holda bu chiziq xatosi — `tashlangan` qatlamiga yoziladi. Qisqartirish faqat *tekshirish* uchun,
     geometriya o'zgartirilmaydi.
3. **Ustiga Ikkilamchi kerakmi?** Xuddi shunday: har bir B poligon uchun I va M qidiriladi (M = Paxta ham kiradi,
   shuning uchun ustida Paxta turgan Ozuqa to'ldirilmaydi).
4. Yangi bo'lakka manbadan `viloyat, tuman, region, district, yil, f_name, f_inn, f_cad` ko'chiriladi;
   `manba_fid`, `manba_turi` yoziladi; `maydon` Albers maydonidan hisoblanadi.
5. `qoshni_turi`: yangi bo'lak 5 m ga kengaytirilib, unga tegadigan shu mavsumdagi ("aniqlanmagan" bo'lmagan)
   poligonlardan kesishmasi eng katta bo'lganining turi olinadi.
6. `ziddiyat`: bir mavsum ichida ustma-ust (> 100 m²) yoki Ikkilamchi Mavsumiy ustida bo'lsa belgilanadi.
7. `dala_id`: asl va yangi bo'laklar graf tugunlari; > 100 m² ustma-ust tushgan juftlar qirra; grafning bog'langan
   komponentlari (scipy `connected_components`) = bitta dala. `dala` qatlami — har komponentning birlashmasi va
   B_ga, I_ga, M_ga yig'indilari.
8. Aniq nusxa bo'laklar uchun natijaga asl EPSG:3857 geometriyasi yoziladi (proyeksiya almashinuvidan
   yaxlitlash xatosi ham qolmasin).
9. **Bo'laklarni ajratish:** ayirma bir nechta alohida qism bersa (masalan 4 ga dalaning o'rtasida 2 ga ikkilamchi,
   ikki chetida 1 ga dan), har bir qism alohida qatorga ajratiladi (`explode`); `maydon` har qism uchun qayta hisoblanadi.
10. **Fermer ma'lumotini o'tkazish:** `f_inn` bo'sh bo'lgan har bir poligon (asl yoki yangi) uchun u bilan
    > 100 m² ustma-ust tushgan, `f_inn` bor **asl** poligonlar olinadi; kesishmasi eng katta bo'lganidan
    `f_name`, `f_inn`, `f_cad` uchalasi birga ko'chiriladi. Manba `fermer_manba_fid` ga yoziladi.
    Ikkinchi, boshqa fermer poligonning > 10% ini egallasa `fermer_aralash = 1` (tekshirish uchun).
11. Jamoa qo'shgan "Ikkilamchi ekin aniqlanmagan" qatorlarda `crop_id`, `vh`, `yld` bo'shatiladi.

### 7.4 Tekshiruvlar (`02b_tekshirish.py`, `02c_teshik_tekshirish.py`)
- Asl qatorlarning barcha ustunlari va geometriyasi v1 bilan bir xilligi (`equals_exact`).
- Aniq nusxa bo'laklar manba bilan koordinatama-koordinata bir xilligi; qisman bo'laklar manbadan chiqmasligi.
- **Balans:** Birlamchi maydoni = Ikkilamchi maydoni + ustida Mavsumiy turgan Birlamchi maydoni.
- **Teshik:** barcha ekin poligonlari birlashmasi minus (B ∪ M) va minus (I ∪ M) — har mavsumda to'liq dalaning
  yopilmagan joyi; haqiqiy teshik (≥ 0.02 ga, eni ≥ 6 m) 0 bo'lishi kerak.

## 8. Qabul qilingan qarorlar (ish doirasi)
- **Yonma-yon bo'laklar bitta `dala_id` ga birlashtirilmaydi.** `dala_id` faqat ustma-ust tushgan bo'laklar guruhi
  bo'lib qoladi. Mavsum to'ldirish har bir joyda alohida ishlaydi, dala chegarasi kerak emas.
- **Ekin turini aniqlash bizning ishimiz emas.** "aniqlanmagan" bo'laklarning turi topilmaydi (NDVI, qo'shni bo'yicha
  taxmin qilinmaydi). `qoshni_turi` faqat ma'lumot uchun qoladi.

- **`crop_id`:** "Ikkilamchi ekin aniqlanmagan" va "Birlamchi ekin aniqlanmagan" uchun **bo'sh qoladi**,
  qishloq jamoasi keyin o'zi yozadi. (Jamoa qo'shgan "Ikkilamchi ekin aniqlanmagan" da crop_id ostidagi birlamchidan
  ko'chirilgan edi: Bug'doy ustida 6, Ozuqa ustida 25.)
- **Ekinga bog'liq ma'lumotlar** (`crop_id`, `vh`, `yld`) jamoa qo'shgan "Ikkilamchi ekin aniqlanmagan" konturlarda
  **tozalanadi** (bug'doyning holati/hosildorligi ko'chirilgan edi). O'zgarmas ma'lumotlar qoladi.
- **O'zgarmas ma'lumotlar** (`f_name`, `f_inn`, `f_cad`; `viloyat`, `tuman`, `region`, `district`, `yil` hammasida bor)
  katta (to'liq) daladan uning ustidagi/ostidagi kichik poligonlarga **o'tkaziladi** — asl ikkilamchilarga ham,
  yangi bo'laklarga ham. Faqat ustma-ust turgan poligondan; yonma-yondan olinmaydi. Mavjud qiymat almashtirilmaydi.
- **Yangi bo'laklar bir-biriga bog'lanmaydi:** har bir alohida qism o'z qatori (bitta qator = bitta Polygon).

- **Tuman chegarasi:** har bir tuman qo'shni tumanlarning chegaradagi poligonlari bilan birga (kontekst) ishlanadi —
  kontekst poligonlar yopuvchi va fermer manbasi bo'la oladi, lekin natijaga faqat o'z tumanida yoziladi.
  (Butun faylda 10 ta joyda, 74.5 ga, kuzgi ekin qo'shni tumandagi bug'doy ustida turibdi.)

## 9. Yakuniy fayl tuzilishi

Bitta GeoPackage, EPSG:3857 (asl shp bilan bir xil), 3 qatlam:

| Qatlam | Ichida |
|---|---|
| `ekin_yerlar` | **hammasi**: barcha asl poligonlar + yangi qo'shilgan bo'laklar (`qoshilgan` ustuni bilan ajratiladi) |
| `qoshilgan` | faqat yangi qo'shilgan bo'laklar (ustunlari `ekin_yerlar` bilan bir xil) |
| `tashlangan` | olib tashlanganlar: (1) Paxta ustidan kesilgan / olib tashlangan Ikkilamchi qismlari, (2) yangi bo'lak yaratilmagan chiziq-xatosi qoldiqlari; `sabab` ustunida qaysi biri |

### Yakuniy eksport: `scripts/05_uniqueid_eksport.py` (qo'lda tuzatishlardan keyin, oxirida bir marta)
```
python scripts/05_uniqueid_eksport.py natija/ekin_yerlar_yakuniy.gpkg natija/ekin_yerlar_toliq.gpkg natija/ekin_yerlar_qisqa.gpkg
```
- **Multipart → Singlepart** (ArcGIS "Multipart To Singlepart" bilan bir xil): bir nechta alohida qismli poligon har bir
  qismi alohida qatorga ajratiladi, atributlar ko'chiriladi, `maydon` har qism uchun alohida. Uchala qatlam va qisqa
  versiya geometriya turi — `Polygon`. To'liq versiyada `qism_no` (1, 2, …) va `qism_soni` (asl poligonda nechta qism
  bo'lgan; 1 = ajratilmagan) ustunlari; `fid_asl` bir xil qoladi (qaysi asl poligondan ekani ko'rinadi).
- **`uniqueid` hamma qatorga (har bir qismga) yangidan beriladi** (UUID4, 32 ta hex belgi, masalan `9dc5c761c51d476cafdf900f5dd1aa2f`);
  eski qiymatlar almashtiriladi. `--format arcgis` → `{07B48855-B4BB-419B-A321-57B2A206DA1D}` ko'rinishi.
  Har ishga tushirishda ID lar yangidan yaratiladi — shuning uchun faqat oxirida bir marta ishlatiladi.
- `maydon` va Shape ustunlari geometriyadan qayta hisoblanadi (qo'lda tahrir qilingan poligonlar uchun ham to'g'ri).
- **To'liq versiya (backup):** barcha ustunlar; `ekin_yerlar`, `qoshilgan` (xuddi shu uniqueid bilan), `tashlangan`.
- **Suv ichish davri** (ikkala versiyada, oy raqami, butun son; ikkala chegara ham kiradi):

  | mavsum | `suv_boshi` | `suv_oxiri` |
  |---|---|---|
  | Birlamchi ekin | 3 (mart) | 5 (may) |
  | Ikkilamchi ekin | 6 (iyun) | 10 (oktyabr) |
  | Mavsumiy ekin | 3 (mart) | 10 (oktyabr) |
  | bo'sh (Baliqxovuz, Issiqxona) | bo'sh | bo'sh |

  Misol (ArcGIS filtr): iyulda suv ichayotganlar — `suv_boshi <= 7 AND suv_oxiri >= 7`.
  Oylar `05_uniqueid_eksport.py` dagi `SUV_OYLARI` lug'atida o'zgartiriladi.
- **Qisqa versiya** (autsorsing kompaniyasi uchun): `viloyat | tuman | maydon | turi | yil | uniqueid | season | suv_boshi | suv_oxiri`
  (`season` = `mavsum`) + geometriya. **Baliqxovuz va Issiqxona qisqa versiyaga kirmaydi** (ekin emas); to'liq versiyada qoladi.
- **Uchala faylda bir xil uniqueid:** 05 oxirida kirish faylini (`ekin_yerlar_yakuniy.gpkg`) to'liq versiya bilan
  almashtiradi (singlepart, xuddi shu ID lar); eski kirish `ekin_yerlar_yakuniy_eski_<vaqt>.gpkg` bo'lib saqlanadi.
  Natijada kirish = to'liq (bir xil qatorlar), qisqa = to'liq minus Baliqxovuz/Issiqxona; bir ID = bir poligon
  (geometriya, turi, maydon bir xil). Kirish ArcGIS da ochiq bo'lsa almashtirib bo'lmaydi — ogohlantirish chiqadi.
  `--kirishga-tegma` bilan bu qadam o'chiriladi.
- **Qisqa versiyani qayta yasash:** `scripts/06_qisqa_versiya.py` (`3_QISQA_QAYTA.bat`) — mavjud to'liq versiyadan,
  uniqueid o'zgarmaydi (05 ni qayta ishlatish ID larni yangilaydi).
- Chiqish fayllari bor bo'lsa ustiga yozmaydi; invalid/bo'sh geometriya bo'lsa ogohlantiradi.

Qishloq jamoasi uchun xatolar ro'yxati: `natija/xatolar_hisoboti.xlsx` (`scripts/04_xatolar_excel.py`) — har bir
varaqning ma'nosi faylning `Izoh` varag'ida.

## 10. Ustunlar lug'ati

### Asl 22 ustun — hammasi saqlanadi
`viloyat, tuman, region, district, maydon, turi, yil, globalid_1, vh, f_name, f_inn, f_cad, uniqueid, yld, crop_id,
yer_turi, ekin_davri, st_area_sh, st_perimet, shape_leng, Shape_Le_1, Shape_Area`

Asl qiymatlarga kiritilgan o'zgarishlar (faqat shular):
| Ustun | O'zgarish |
|---|---|
| matn ustunlari | apostroflar `'` ga keltirilgan (`turi`, `vh`, `tuman`, `f_name`) |
| `f_name`, `f_inn`, `f_cad` | faqat **bo'sh** bo'lsa, ustma-ust turgan katta daladan to'ldirilgan |
| `crop_id`, `vh`, `yld` | jamoa qo'shgan "Ikkilamchi ekin aniqlanmagan" qatorlarda bo'shatilgan |
| `st_area_sh`, `Shape_Area` | **tuzatilgan**: haqiqiy (geodezik, WGS84 ellipsoid) maydon, m² (avval Mercatorda ~1.69x katta yoki 0) |
| `st_perimet`, `shape_leng`, `Shape_Le_1` | **tuzatilgan**: haqiqiy (geodezik) perimetr, m (avval Mercatorda yoki 0) |
| `maydon` | **qayta hisoblangan** (qaror): hamma qatorda geometriyadan haqiqiy (geodezik) maydon, ga; 99.9% qatorda farq < 0.1% |
| geometriya | faqat 2 holatda o'zgargan: buzuq geometriya tuzatilgan (`geom_tuzatildi = 1`) yoki Paxta ustidagi qismi kesilgan (`kesildi = 1`) |

### Biz qo'shgan ustunlar
| Ustun | Ma'nosi |
|---|---|
| `fid_asl` | asl shp dagi qator raqami (FID); yangi qatorlarda bo'sh |
| `geom_tuzatildi` | 1 = buzuq (invalid) geometriya `make_valid` bilan tuzatilgan |
| `mavsum` | Birlamchi ekin / Ikkilamchi ekin / Mavsumiy ekin (2-bo'lim qoidalari); Baliqxovuz, Issiqxona — bo'sh |
| `qoshilgan` | 0 = asl poligon, 1 = biz qo'shgan yangi bo'lak |
| `dala_id` | ustma-ust tushgan bo'laklar guruhi (bir joydagi Birlamchi + Ikkilamchi); yonma-yonlar birlashtirilmagan |
| `ziddiyat` | bir mavsum ichida ustma-ust yoki Ikkilamchi Mavsumiy ustida turgan bo'lsa — izoh |
| `fermer_manba_fid` | fermer ma'lumoti qaysi asl poligondan (`fid_asl`) o'tkazilgani; bo'sh = o'tkazilmagan |
| `fermer_aralash` | 1 = poligon ikki xil fermer dalasi ustiga tushadi (tekshirish kerak) |
| `manba_fid` | yangi bo'lak qaysi asl poligondan (`fid_asl`) olingani |
| `manba_turi` | o'sha manba poligonning `turi` |
| `qoshni_turi` | 5 m ichida tegib turgan eng katta shu mavsumdagi ekin — faqat ma'lumot, tur aniqlash uchun emas |
| `aniq_nusxa` | 1 = yangi bo'lak manbaning aynan nusxasi, 0 = manba minus yopuvchi poligonlar (ayirma) |
| `kesildi` | 1 = asl Ikkilamchi konturning Paxta (Mavsumiy) ustidagi qismi kesilgan |

`tashlangan` qatlami ustunlari: `manba_fid` (asl `fid_asl`), `manba_turi`, `sabab`, `yetishmagan` (chiziq xatosida qaysi mavsum
yetishmagan), `maydon_m2`, `viloyat`, `tuman`.

## 11. Ochiq savollar
- Qishloq jamoasi `xatolar_hisoboti.xlsx` bo'yicha tuzatishlar kiritadi; `crop_id` ni "aniqlanmagan" turlarga ular yozadi.
