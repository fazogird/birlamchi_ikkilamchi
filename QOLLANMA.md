# Foydalanuvchi qo'llanmasi: ekin yerlari — mavsum va to'liq dala

Bu dastur qishloq xo'jaligi loyihasidan kelgan ekin yerlari shp faylini olib:
- har bir poligonga to'g'ri **mavsum** (Birlamchi / Ikkilamchi / Mavsumiy) beradi,
- to'liq dalani **har mavsumda to'liq yopadi** (yetishmagan qismlarga "aniqlanmagan" qo'shadi),
- fermer ma'lumotlarini katta daladan kichik dalalarga o'tkazadi, maydonlarni tuzatadi,
- qishloq jamoasi uchun **xatolar ro'yxatini (Excel)** chiqaradi,
- oxirida **uniqueid**, **suv ichish oylari** bilan **to'liq** va **qisqa** versiyani saqlaydi.

Qoidalar va ustunlar ma'nosi: [QOIDALAR.md](QOIDALAR.md).

---

## 0. Bir marta tayyorlanadi

**Kerak:** Windows, Miniconda va unda `gis_pro` muhiti (geopandas, pyogrio, shapely 2, pyproj, scipy, openpyxl).

Yangi kompyuterda muhit yo'q bo'lsa, **Anaconda Prompt** da:
```
conda create -n gis_pro -c conda-forge python=3.10 geopandas pyogrio shapely pyproj scipy openpyxl
```

`.bat` fayllar muhitni `%LOCALAPPDATA%\miniconda3\envs\gis_pro` dan qidiradi. Boshqa joyda bo'lsa, `.bat` faylni
Bloknotda ochib `set "ENV=..."` qatoriga to'g'ri yo'lni yozing.

**Papka tuzilishi** (butun papkani ko'chirib berish kifoya):
```
bir_ikki_lamchi\
  1_TAYYORLASH.bat      <- 1-bosqich (ikki marta bosiladi)
  2_EKSPORT.bat         <- 2-bosqich (ikki marta bosiladi)
  3_QISQA_QAYTA.bat     <- qo'shimcha: to'liqdan qisqa versiyani qayta yasash (ID o'zgarmaydi)
  pipeline.py           <- asosiy dastur (bat shuni chaqiradi)
  scripts\              <- 01..05 modullar
  QOLLANMA.md, QOIDALAR.md
```

**Kirish shp talabi:** asl loyiha shp tuzilishi (22 ustun): `viloyat, tuman, region, district, maydon, turi, yil,
f_name, f_inn, f_cad, crop_id, vh, yld, ekin_davri, st_area_sh, st_perimet, shape_leng, Shape_Le_1, Shape_Area, ...`.
`viloyat` va `tuman` bo'sh bo'lmasligi kerak. Ustun yetishmasa dastur boshidayoq aytadi va to'xtaydi.

---

## 1-BOSQICH: Tayyorlash (asl shp → yakuniy fayl + Excel)

1. **`1_TAYYORLASH.bat`** ni ikki marta bosing.
2. Oyna chiqadi — **asl shp faylni tanlang**.
3. Dastur o'zi ishlaydi (qora oynada jarayon ko'rinadi). 500 ming poligon uchun **~12–15 daqiqa**:
   | Qadam | Nima qiladi | Vaqt (500k) |
   |---|---|---|
   | 1/4 | apostrof, buzuq geometriya, `mavsum` ustuni | ~2 daq |
   | 2/4 | mavsumlarni to'ldirish, Paxta qoidasi, fermer ma'lumoti, maydon (parallel) | ~3–4 daq |
   | 3/4 | yakuniy tekshiruv (asl ma'lumot saqlanganmi, balans, teshik) | ~7 daq |
   | 4/4 | xatolar hisoboti (Excel) | ~0.5 daq |
4. Oxirida "1-BOSQICH TUGADI" va fayllar yo'li chiqadi. Natija **yangi papkaga** yoziladi:
   `natija_<shp nomi>_<sana_vaqt>\`

| Fayl | Nima |
|---|---|
| `ekin_yerlar_yakuniy.gpkg` | **asosiy natija** (3 qatlam: `ekin_yerlar` — hammasi, `qoshilgan`, `tashlangan`) |
| `xatolar_hisoboti.xlsx` | qishloq jamoasi tekshiradigan ro'yxatlar (`Izoh` varag'ida har varaq ma'nosi) |
| `ekin_yerlar_v1.gpkg` | oraliq fayl (1-qadam natijasi) |
| `ekin_yerlar_yakuniy_tuman_balans.csv` | har tuman balansi |
| `jurnal.txt` | hamma qadamlar jurnali (muammo bo'lsa shuni yuboring) |

**3/4 tekshiruvda nimaga qarash kerak** (`jurnal.txt` da):
`ruxsatsiz_ozgarish = 0`, `invalid = 0`, `fid_toliq = True`, "balki muammoli tumanlar: yo'q".
Tuman ichida "teshik" chiqsa — odatda tuman chegarasidagi holat (Excel `Tuman_chegarasi` varag'i).

---

## Oraliq: qo'lda tekshirish va tuzatish (ArcGIS)

1. `xatolar_hisoboti.xlsx` ni oching, ayniqsa: `Paxta_ustida_ikkilamchi`, `Tuman_chegarasi`, `Fermer_aralash`, `Ziddiyat`.
   Kerak bo'lsa qishloq jamoasiga yuboring.
2. ArcGIS da `ekin_yerlar_yakuniy.gpkg` → `ekin_yerlar` qatlamini oching, `fid_asl` bo'yicha topib tuzating.
3. **Save Edits** qiling. (Tuzatish shart bo'lmasa — bu qadam o'tkazib yuboriladi.)

---

## 2-BOSQICH: Eksport (tuzatilgan fayl → to'liq va qisqa versiya)

1. **`2_EKSPORT.bat`** ni ikki marta bosing.
2. Oyna chiqadi — **tuzatilgan `ekin_yerlar_yakuniy.gpkg`** ni tanlang.
3. ~2–3 daqiqa (500k). Natija o'sha papkaga:

| Fayl | Nima |
|---|---|
| `ekin_yerlar_toliq_<sana_vaqt>.gpkg` | **to'liq backup**: barcha ustunlar, 3 qatlam |
| `ekin_yerlar_qisqa_<sana_vaqt>.gpkg` | **qisqa** (autsorsing uchun): `viloyat, tuman, maydon, turi, yil, uniqueid, season, suv_boshi, suv_oxiri`; **Baliqxovuz va Issiqxona kirmaydi** (ular faqat to'liq versiyada) |

Bu bosqichda:
- **Multipart → Singlepart**: bir nechta qismli poligonlar alohida qatorlarga ajratiladi;
- har qatorga **yangi `uniqueid`** (32 hex belgi). ArcGIS ko'rinishi `{XXXXXXXX-...}` kerak bo'lsa:
  `2_EKSPORT.bat --format arcgis` (cmd dan);
- `maydon` geometriyadan qayta hisoblanadi (qo'lda tahrir qilingan poligonlar uchun ham);
- suv ichish oylari: Birlamchi 3–5, Ikkilamchi 6–10, Mavsumiy 3–10.

**Uchala faylda ID bir xil:** 2-bosqich oxirida kirish fayli (`ekin_yerlar_yakuniy.gpkg`) ham to'liq versiya bilan
almashtiriladi — endi `yakuniy`, `toliq` va `qisqa` da bir poligon = bitta va bir xil `uniqueid`. Eski `yakuniy`
`ekin_yerlar_yakuniy_eski_<sana_vaqt>.gpkg` bo'lib saqlanadi. **2-bosqichdan oldin ArcGIS da faylni yoping**
(ochiq bo'lsa almashtirib bo'lmaydi va ogohlantirish chiqadi).

⚠ `uniqueid` har ishga tushirishda **yangidan** yaratiladi — 2-bosqichni faqat oxirida bir marta qiling
(yoki qayta qilsangiz, eski ID lar bilan bog'langan narsa bo'lmasin). Fayl nomida sana-vaqt bor, eskisi o'chmaydi.

---

## QO'SHIMCHA: qisqa versiyani qayta yasash (uniqueid o'zgarmaydi)

To'liq versiya allaqachon bor, faqat qisqa versiyani qaytadan olish kerak bo'lsa (masalan, qoida o'zgargan yoki
qisqa fayl yo'qolgan) — **2-bosqichni qayta ishlatmang** (u uniqueid larni yangilaydi). Buning o'rniga:

1. **`3_QISQA_QAYTA.bat`** ni ikki marta bosing.
2. **`ekin_yerlar_toliq_<sana_vaqt>.gpkg`** ni tanlang.
3. Yangi `ekin_yerlar_qisqa_<sana_vaqt>.gpkg` yoziladi — uniqueid lar to'liq versiya bilan **bir xil**,
   Baliqxovuz va Issiqxona chiqarilgan. Eski fayllar o'chmaydi.

---

## Buyruq satridan (ixtiyoriy)

Anaconda Prompt da, `conda activate gis_pro` dan keyin, loyiha papkasida:
```
python pipeline.py tayyorla --shp D:\yo'l\asl.shp --papka D:\yo'l\natija_papka
python pipeline.py eksport  --kirish D:\yo'l\natija_papka\ekin_yerlar_yakuniy.gpkg --format hex
python pipeline.py qisqa    --kirish D:\yo'l\natija_papka\ekin_yerlar_toliq_<sana_vaqt>.gpkg
```
`--ishchi 8` — parallel jarayonlar soni (standart: yadrolar − 2, ko'pi bilan 12; xotira kam bo'lsa kamaytiring).

---

## Muammo bo'lsa

| Xabar | Nima qilish |
|---|---|
| `gis_pro muhiti topilmadi` | `.bat` dagi `ENV` qatoriga muhit yo'lini yozing |
| `shp da quyidagi ustunlar yo'q` | shp tuzilishi boshqa — yetishmagan ustunlarni qo'shing yoki to'g'ri faylni tanlang |
| `viloyat yoki tuman bo'sh` | shp da o'sha qatorlarni to'ldiring |
| `natija fayllari allaqachon bor` | boshqa (bo'sh) papka tanlang — dastur hech qachon ustiga yozmaydi |
| `XATO: '...' bosqichi to'xtadi` | `jurnal.txt` ni oching, oxirgi xabarni o'qing yoki yuboring |
| `invalid geometriya ... ta` (2-bosqich) | qo'lda tahrirdan buzilgan poligon — ArcGIS da *Repair Geometry* qilib qayta ishga tushiring |

## Qoidalarni o'zgartirish (dasturchi uchun)

| Nima | Qayerda |
|---|---|
| `turi` / `ekin_davri` → `mavsum` | `scripts/01_atribut_mavsum.py`: `MAVSUM_TURI`, `MAVSUM_DAVR` |
| chiziq xatosi chegaralari (6 m, 0.02 ga), ustma-ustlik (100 m²) | `scripts/02_dala_toldirish.py` boshida |
| suv ichish oylari | `scripts/05_uniqueid_eksport.py`: `SUV_OYLARI` |
| qisqa versiya ustunlari | `scripts/05_uniqueid_eksport.py`: `QISQA` |
| qisqa versiyaga kirmaydigan turlar (Baliqxovuz, Issiqxona) | `scripts/05_uniqueid_eksport.py`: `QISQA_CHIQARILADI` (06 ham shundan oladi) |
