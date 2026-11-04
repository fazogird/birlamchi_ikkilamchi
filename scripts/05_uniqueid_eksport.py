"""
5-modul: uniqueid berish, to'liq backup va qisqa versiya.

Kirish: yakuniy GeoPackage (qo'lda tuzatilgan bo'lishi mumkin), qatlam `ekin_yerlar`.
Nima qiladi:
  0. Multipart -> Singlepart (ArcGIS "Multipart To Singlepart" bilan bir xil): bir nechta alohida qismdan iborat
     poligon har bir qism alohida qator bo'lib ajratiladi; barcha atributlar qismlarga ko'chiriladi.
     To'liq versiyada `qism_no` (1, 2, ...; bitta qismli = 1) va `qism_soni` ustunlari qo'shiladi.
  1. Har bir qatorga (qismga) YANGI `uniqueid` beriladi (UUID4, 32 ta hex belgi). Eski qiymatlar almashtiriladi.
  2. `maydon` (ga) va Shape ustunlari geometriyadan qayta hisoblanadi (qo'lda tahrirdan keyin ham to'g'ri bo'lsin).
  3. TO'LIQ versiya (backup): barcha ustunlar; qatlamlar `ekin_yerlar`, `qoshilgan` (= ekin_yerlar dagi qoshilgan=1,
     xuddi shu uniqueid bilan), `tashlangan` (o'zgarishsiz ko'chiriladi).
  4. Suv ichish davri (oy raqami, ikkala versiyada): suv_boshi, suv_oxiri
       Birlamchi ekin 3–5 | Ikkilamchi ekin 6–10 | Mavsumiy ekin 3–10 | mavsumi yo'q (Baliqxovuz, Issiqxona) — bo'sh
  5. QISQA versiya: viloyat | tuman | maydon | turi | yil | uniqueid | season (= mavsum) | suv_boshi | suv_oxiri + geometriya.
     Baliqxovuz va Issiqxona qisqa versiyaga KIRMAYDI (to'liq versiyada qoladi).

  6. KIRISH fayli ham yangilanadi: u to'liq versiya bilan almashtiriladi (singlepart, xuddi shu uniqueid lar) —
     shunda kirish, to'liq va qisqa versiyada bir poligon = bitta va bir xil uniqueid. Eski kirish
     `<nom>_eski_<vaqt>.gpkg` bo'lib saqlanadi. O'chirish uchun: --kirishga-tegma

Chiqish fayllari mavjud bo'lsa ustiga yozilmaydi.
DIQQAT: har ishga tushirishda uniqueid lar yangidan yaratiladi (uchala faylda birga) — faqat oxirida bir marta.

python 05_uniqueid_eksport.py <kirish.gpkg> <toliq.gpkg> <qisqa.gpkg> [--format hex|arcgis] [--kirishga-tegma]
  --format hex     (standart) 32 ta kichik hex belgi:            3f2a9c4e8b7d41f6a0c5e19d2b7f8a61
  --format arcgis  ArcGIS GUID ko'rinishi (32 hex + chiziq, {}): {3F2A9C4E-8B7D-41F6-A0C5-E19D2B7F8A61}
"""
import os, sys, time, uuid, shutil
import numpy as np, pandas as pd, pyogrio, shapely
from pyproj import Geod

GEOD = Geod(ellps="WGS84")
AREA_COLS = ["st_area_sh", "Shape_Area"]
LEN_COLS = ["st_perimet", "shape_leng", "Shape_Le_1"]
QISQA = ["viloyat", "tuman", "maydon", "turi", "yil", "uniqueid", "season", "suv_boshi", "suv_oxiri"]
# qisqa versiyaga (autsorsing uchun) kirmaydigan turlar — ekin emas; to'liq versiyada qoladi
QISQA_CHIQARILADI = ["Baliqxovuz", "Issiqxona"]
# mavsum -> (suv ichish boshlanadigan oy, tugaydigan oy), ikkalasi ham kiradi
SUV_OYLARI = {"Birlamchi ekin": (3, 5), "Ikkilamchi ekin": (6, 10), "Mavsumiy ekin": (3, 10)}


def new_ids(n, fmt):
    if fmt == "arcgis":
        return ["{" + str(uuid.uuid4()).upper() + "}" for _ in range(n)]
    return [uuid.uuid4().hex for _ in range(n)]


def singlepart(df):
    """Multipart To Singlepart: har bir Polygon qismi alohida qator; qism_no / qism_soni qo'shiladi."""
    n0 = len(df)
    nparts = shapely.get_num_geometries(df.geometry.values)
    had = "qism_no" in df.columns and "qism_soni" in df.columns    # oldin ajratilgan fayl qayta kirsa
    out = df.explode(index_parts=True)
    rep = np.repeat(nparts, np.maximum(nparts, 1))[: len(out)]
    new_no, new_soni = out.index.get_level_values(1).values + 1, rep
    if had:   # hozir ajratilmagan qatorlarda oldingi qism_no / qism_soni saqlanadi
        old_no = pd.to_numeric(out["qism_no"], errors="coerce").fillna(1).values
        old_soni = pd.to_numeric(out["qism_soni"], errors="coerce").fillna(1).values
        new_no, new_soni = np.where(rep > 1, new_no, old_no), np.where(rep > 1, rep, old_soni)
    out["qism_no"], out["qism_soni"] = new_no.astype("int32"), new_soni.astype("int32")
    out = out.reset_index(drop=True)
    out = out[out.geometry.geom_type == "Polygon"].reset_index(drop=True)
    return out, n0, int((nparts > 1).sum())


def geodesic(geoms_4326):
    a, p = np.empty(len(geoms_4326)), np.empty(len(geoms_4326))
    for k, gm in enumerate(geoms_4326):
        ar, pr = GEOD.geometry_area_perimeter(gm)
        a[k], p[k] = abs(ar), pr
    return a, p


def main(src, toliq, qisqa, fmt, kirishni_yangila=True):
    for f in (toliq, qisqa):
        if os.path.exists(f):
            raise SystemExit(f"Chiqish fayli bor, ustiga yozmayman: {f}")
    t0 = time.time()
    y = pyogrio.read_dataframe(src, layer="ekin_yerlar")
    need = ["viloyat", "tuman", "maydon", "turi", "yil", "mavsum", "qoshilgan"]
    miss = [c for c in need if c not in y.columns]
    if miss:
        raise SystemExit(f"Kirish faylida ustun yo'q: {miss}")
    n_inv = int((~y.geometry.is_valid).sum())
    n_empty = int((y.geometry.isna() | y.geometry.is_empty).sum())
    y = y[~(y.geometry.isna() | y.geometry.is_empty)].reset_index(drop=True)

    # 0. multipart -> singlepart
    y, n_before, n_multi = singlepart(y)

    # 1. yangi uniqueid
    y["uniqueid"] = new_ids(len(y), fmt)
    assert y.uniqueid.is_unique
    # 2. maydon va Shape ustunlari geometriyadan
    ok = ~(y.geometry.isna() | y.geometry.is_empty)
    ar, pr = np.full(len(y), np.nan), np.full(len(y), np.nan)
    a_, p_ = geodesic(y.geometry[ok].to_crs(4326).values)
    ar[ok.values], pr[ok.values] = a_, p_
    y["maydon"] = ar / 1e4
    for c in AREA_COLS:
        if c in y.columns: y[c] = np.round(ar, 2)
    for c in LEN_COLS:
        if c in y.columns: y[c] = np.round(pr, 2)

    # suv ichish davri (oy raqami)
    y["suv_boshi"] = y.mavsum.map({k: v[0] for k, v in SUV_OYLARI.items()}).astype("Int8")
    y["suv_oxiri"] = y.mavsum.map({k: v[1] for k, v in SUV_OYLARI.items()}).astype("Int8")

    # 3. to'liq versiya (hamma qatlam singlepart, geometriya turi Polygon)
    pyogrio.write_dataframe(y, toliq, layer="ekin_yerlar", driver="GPKG", promote_to_multi=False, geometry_type="Polygon")
    q = y[pd.to_numeric(y.qoshilgan, errors="coerce").fillna(0) == 1]
    if len(q):
        pyogrio.write_dataframe(q, toliq, layer="qoshilgan", driver="GPKG", promote_to_multi=False, geometry_type="Polygon", append=True)
    layers = [l for l, _ in pyogrio.list_layers(src)]
    if "tashlangan" in layers:
        tsh = pyogrio.read_dataframe(src, layer="tashlangan")
        tsh = tsh[~(tsh.geometry.isna() | tsh.geometry.is_empty)]
        if len(tsh):
            tsh, _, _ = singlepart(tsh.reset_index(drop=True))
            pyogrio.write_dataframe(tsh, toliq, layer="tashlangan", driver="GPKG", promote_to_multi=False, geometry_type="Polygon", append=True)

    # 4. qisqa versiya (Baliqxovuz, Issiqxona chiqariladi)
    s = y[~y.turi.isin(QISQA_CHIQARILADI)].rename(columns={"mavsum": "season"})[QISQA + ["geometry"]]
    pyogrio.write_dataframe(s, qisqa, layer="ekin_yerlar", driver="GPKG", promote_to_multi=False, geometry_type="Polygon")
    print(f"Qisqa versiya: {len(s)} qator ({', '.join(QISQA_CHIQARILADI)} chiqarildi: {len(y) - len(s)} ta)")

    print(f"Multipart -> Singlepart: {n_before} qator -> {len(y)} qator ({n_multi} ta multipart poligon ajratildi)")
    print(f"Qatorlar: {len(y)} (shundan qo'shilgan {len(q)}) | yangi uniqueid: {len(y)} ta, takrorsiz: {y.uniqueid.is_unique}")
    print(f"Format: {fmt}, namuna: {y.uniqueid.iloc[0]}")
    print("Suv davri:", y.groupby(y.mavsum.fillna("— (bo'sh)"), dropna=False)[["suv_boshi", "suv_oxiri"]]
          .agg(lambda s: s.dropna().unique().tolist()).to_dict("index"))
    print(f"Ogohlantirish: invalid geometriya {n_inv} ta, bo'sh geometriya {n_empty} ta" if (n_inv or n_empty) else "Geometriya: hammasi yaroqli")
    print(f"To'liq: {toliq}  ({[l for l, _ in pyogrio.list_layers(toliq)]})")
    print(f"Qisqa:  {qisqa}  (ustunlar: {QISQA})")

    # 6. kirish faylini ham xuddi shu ID lar bilan yangilash: kirish = to'liq versiya (uchala fayl bir xil ID)
    if kirishni_yangila:
        bak = os.path.splitext(src)[0] + f"_eski_{time.strftime('%Y%m%d_%H%M%S')}.gpkg"
        try:
            os.replace(src, bak)
            shutil.copyfile(toliq, src)
            print(f"Kirish fayli yangilandi (to'liq versiya bilan bir xil, ID lar mos): {src}")
            print(f"Kirishning eski nusxasi: {bak}")
        except OSError as e:
            print(f"OGOHLANTIRISH: kirish faylini yangilab bo'lmadi ({e}).\n"
                  f"  Fayl ArcGIS da ochiq bo'lishi mumkin. ArcGIS ni yopib, {toliq} ni {src} o'rniga qo'lda nusxalang.\n"
                  f"  To'liq va qisqa versiya ID lari baribir o'zaro mos.")
    print(f"Vaqt: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    a = sys.argv[1:]
    fmt = a[a.index("--format") + 1] if "--format" in a else "hex"
    if fmt not in ("hex", "arcgis"):
        raise SystemExit("--format hex yoki arcgis bo'lishi kerak")
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and not (i > 0 and a[i - 1] == "--format")]
    main(pos[0], pos[1], pos[2], fmt, kirishni_yangila="--kirishga-tegma" not in a)
