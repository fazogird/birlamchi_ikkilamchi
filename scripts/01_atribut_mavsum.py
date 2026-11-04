"""
1-bosqich: atributlarni tozalash va mavsumni belgilash.

Asl shp ga TEGMAYDI. Natija yangi GeoPackage ga yoziladi (dbf 2 GB chegarasi sababli).

Nima qiladi:
  1. Barcha matn ustunlarida apostroflarni bir xil qiladi:  ‘ ’ ʻ ʼ ` ´  ->  '
  2. Buzuq (invalid) geometriyalarni make_valid bilan tuzatadi (faqat poligon qismlari qoladi)
  3. Yangi `mavsum` ustuni (asl `ekin_davri` o'zgarmaydi):
       Bug'doy, Ozuqa                    -> Birlamchi ekin
       Paxta, Bog', Boshqa               -> Mavsumiy ekin   (Boshqa = turi aniqlanmagan ekin)
       Ikkilamchi ekin aniqlanmagan      -> Ikkilamchi ekin
       ekin_davri = Bahorgi              -> Birlamchi ekin
       ekin_davri = Kuzgi                -> Ikkilamchi ekin
       ekin_davri = Mavsumiy             -> Mavsumiy ekin
       Baliqxovuz, Issiqxona             -> bo'sh (ekin emas)
  4. Qo'shimcha ustunlar: fid_asl (asl shp dagi FID), geom_tuzatildi (0/1)

Ishga tushirish (gis_pro muhitida):
  python 01_atribut_mavsum.py <kirish.shp> <chiqish.gpkg>
"""
import os, sys, time
import numpy as np, pandas as pd, pyogrio, shapely

APOS = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "´": "'"})

MAVSUM_TURI = {
    "Bug'doy": "Birlamchi ekin",
    "Ozuqa": "Birlamchi ekin",
    "Paxta": "Mavsumiy ekin",
    "Bog'": "Mavsumiy ekin",
    "Boshqa": "Mavsumiy ekin",
    "Ikkilamchi ekin aniqlanmagan": "Ikkilamchi ekin",
}
MAVSUM_DAVR = {"Bahorgi": "Birlamchi ekin", "Kuzgi": "Ikkilamchi ekin", "Mavsumiy": "Mavsumiy ekin"}
# Viloyatlar ro'yxati qattiq yozilmaydi — kirish faylining o'zidan olinadi (har qanday shp uchun ishlaydi).


def fix_apos(df, stats):
    for c in df.columns:
        if df[c].dtype == object and c != "geometry":
            s = df[c]
            mask = s.notna()
            new = s[mask].astype(str).str.translate(APOS)
            changed = int((new != s[mask]).sum())
            if changed:
                stats[c] = stats.get(c, 0) + changed
                df.loc[mask, c] = new
    return df


def polygonal(geoms):
    """make_valid -> faqat Polygon/MultiPolygon qismlarini qoldiradi."""
    out = []
    for g in geoms:
        g = shapely.make_valid(g)
        if g.geom_type in ("Polygon", "MultiPolygon"):
            out.append(g)
            continue
        parts = [p for p in shapely.get_parts(g) if p.geom_type in ("Polygon", "MultiPolygon")]
        out.append(shapely.union_all(parts) if parts else None)
    return np.array(out, dtype=object)


def mavsum(turi, davr):
    if turi in MAVSUM_TURI:
        return MAVSUM_TURI[turi]
    return MAVSUM_DAVR.get(davr)


def main(src, dst):
    if os.path.exists(dst):
        sys.exit(f"Chiqish fayli allaqachon bor, ustiga yozmayman: {dst}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    total_info = pyogrio.read_info(src, encoding="utf-8")
    apos_stats, inv_total, n_total, empty_after = {}, 0, 0, 0
    vils = pyogrio.read_dataframe(src, columns=["viloyat"], read_geometry=False, encoding="utf-8").viloyat
    vil_list = sorted(vils.dropna().unique().tolist()) + ([None] if vils.isna().any() else [])
    for i, v in enumerate(vil_list):
        t = time.time()
        where = "viloyat IS NULL" if v is None else "viloyat = '{}'".format(v.replace("'", "''"))
        g = pyogrio.read_dataframe(src, where=where, encoding="utf-8", fid_as_index=True)
        g.insert(0, "fid_asl", g.index.values.astype("int64"))
        g = g.reset_index(drop=True)
        g = fix_apos(g, apos_stats)
        inv = ~g.geometry.is_valid
        g["geom_tuzatildi"] = inv.astype("int8")
        if inv.any():
            g.loc[inv, "geometry"] = polygonal(g.geometry.values[inv.values])
            empty_after += int(g.geometry[inv].isna().sum())
        g["mavsum"] = [mavsum(t_, d_) for t_, d_ in zip(g["turi"], g["ekin_davri"])]
        # shapefile dbf dan qolgan bo'sh string o'rniga NULL
        for c in ["ekin_davri", "yer_turi", "vh", "f_name", "f_inn", "f_cad", "uniqueid", "globalid_1"]:
            if c in g.columns:
                g.loc[g[c].astype(str).str.strip().isin(["", "None"]), c] = None
        pyogrio.write_dataframe(g, dst, layer="ekin_yerlar", driver="GPKG", promote_to_multi=True,
                                append=i > 0, encoding="utf-8")
        n_total += len(g); inv_total += int(inv.sum())
        print(f"{v}: {len(g)} ta, invalid tuzatildi={int(inv.sum())}  ({time.time()-t:.0f}s)", flush=True)
    print(f"\nJami yozildi: {n_total} / asl {total_info['features']}")
    print(f"Invalid tuzatildi: {inv_total}, tuzatishdan keyin bo'sh qolgan: {empty_after}")
    print("Apostrof almashtirilgan qatorlar (ustun bo'yicha):", apos_stats)
    if n_total != total_info["features"]:
        sys.exit(f"XATO: {total_info['features'] - n_total} ta qator yozilmadi")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
