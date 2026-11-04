"""Yakuniy GeoPackage ni butunlay tekshirish — tumanma-tuman, parallel.
python 03_yakuniy_tekshirish.py <v1.gpkg> <yakuniy.gpkg> [--ishchi 12]"""
import os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd, pyogrio, shapely

AEA = "+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=67 +datum=WGS84 +units=m +no_defs"
FERMER = ["f_name", "f_inn", "f_cad"]; EKIN = ["crop_id", "vh", "yld"]; IK = "Ikkilamchi ekin aniqlanmagan"
SHAPE = ["st_area_sh", "st_perimet", "shape_leng", "Shape_Le_1", "Shape_Area"]
CLS = {"Birlamchi ekin": "B", "Ikkilamchi ekin": "I", "Mavsumiy ekin": "M"}
ASL22 = ["viloyat", "tuman", "region", "district", "maydon", "turi", "yil", "globalid_1", "vh", "f_name", "f_inn", "f_cad",
         "uniqueid", "yld", "crop_id", "yer_turi", "ekin_davri"] + SHAPE
emp = lambda s: s.isna() | s.astype(str).str.strip().isin(["", "None", "nan"])


def safe_union(arr):
    if not len(arr):
        return shapely.Polygon()
    try:
        return shapely.union_all(arr)
    except shapely.errors.GEOSException:
        return shapely.union_all(shapely.make_valid(shapely.set_precision(arr, 0.01)))


def real_area(h):
    return sum(p.area for p in shapely.get_parts(h) if p.area >= 200 and not p.buffer(-3, join_style="mitre").is_empty)


def check(v1, out, vil, tm):
    q = lambda s: s.replace("'", "''")
    w = f"viloyat = '{q(vil)}' AND tuman = '{q(tm)}'"
    a = pyogrio.read_dataframe(v1, layer="ekin_yerlar", where=w).sort_values("fid_asl").reset_index(drop=True)
    o = pyogrio.read_dataframe(out, layer="ekin_yerlar", where=w)
    has_t = "tashlangan" in [l for l, _ in pyogrio.list_layers(out)]
    tq = pyogrio.read_dataframe(out, layer="tashlangan", where=w, read_geometry=False) if has_t else pd.DataFrame(columns=["sabab", "manba_fid"])
    old = o[o.qoshilgan == 0].sort_values("fid_asl").reset_index(drop=True)
    new = o[o.qoshilgan == 1]
    removed = set(tq.loc[tq.sabab.astype(str).str.contains("olib tashlandi"), "manba_fid"].astype(int)) if len(tq) else set()
    r = dict(viloyat=vil, tuman=tm, asl_v1=len(a), asl_natija=len(old), yangi=len(new), olib_tashlangan_asl=len(removed),
             fid_toliq=bool(set(a.fid_asl) - set(old.fid_asl) == removed and old.fid_asl.is_unique
                            and set(old.fid_asl) <= set(a.fid_asl)))
    a = a[~a.fid_asl.isin(removed)].reset_index(drop=True)
    kes = old.kesildi.values == 1
    r["kesilgan_asl"] = int(kes.sum())
    r["geom_bir_xil(kesilmaganlar)"] = bool(shapely.equals_exact(old.geometry.values[~kes], a.geometry.values[~kes], 1e-6).all())
    r["kesilganlar_asl_ichida"] = bool((shapely.area(shapely.difference(old.geometry.values[kes], a.geometry.values[kes])) < 1).all())
    ik = a.turi == IK
    bad = {}
    for c in [c for c in a.columns if c != "geometry"]:
        ch = ~((old[c] == a[c]) | (old[c].isna() & a[c].isna()))
        if c in FERMER: ill = ch & ~emp(a[c])
        elif c in EKIN: ill = ch & ~(ik & emp(old[c]))
        elif c in SHAPE or c == "maydon": ill = ch & False
        else: ill = ch
        if ill.any(): bad[c] = int(ill.sum())
    r["ruxsatsiz_ozgarish"] = bad
    r["fermer_otkazildi"] = int((emp(a.f_inn) & ~emp(old.f_inn)).sum())
    r["ik_tozalandi"] = bool(all(emp(old.loc[ik, c]).all() for c in EKIN))
    g = o.to_crs(AEA)
    ta = g.geometry.area.values
    big = ta > 1.0
    r["maydon_max_farq_%"] = float(np.abs(o.maydon.values[big] * 1e4 / ta[big] - 1).max() * 100) if big.any() else 0.0
    r["Shape_max_farq_%"] = float(np.abs(o.Shape_Area.values[big] / ta[big] - 1).max() * 100) if big.any() else 0.0
    r["invalid"] = int((~o.geometry.is_valid).sum())
    r["yangi_kop_qismli"] = int((shapely.get_num_geometries(new.geometry.values) > 1).sum())
    r["yangi_crop_id_bosh"] = bool(emp(new.crop_id).all())
    # balans va teshik
    inv = ~g.geometry.is_valid
    if inv.any():
        g.loc[inv, "geometry"] = shapely.make_valid(g.geometry.values[inv.values])
    geo, c = g.geometry.values, g.mavsum.map(CLS).fillna("-").values
    A = lambda m: shapely.area(geo[m]).sum() / 1e4
    U = lambda m: safe_union(geo[m])
    crop = U(c != "-"); UB, UI, UM = U(c == "B"), U(c == "I"), U(c == "M")
    hB = shapely.difference(crop, safe_union(np.array([UB, UM], dtype=object)))
    hI = shapely.difference(crop, safe_union(np.array([UI, UM], dtype=object)))
    bm = shapely.difference(shapely.intersection(UB, UM), UI).area / 1e4
    im = shapely.difference(shapely.intersection(UI, UM), UB).area / 1e4
    b = dict(viloyat=vil, tuman=tm, asl=len(old), yangi=len(new), B_ga=round(A(c == "B")), I_ga=round(A(c == "I")),
             B_M_ostida=round(bm, 1), I_M_ustida=round(im, 1), farq_ga=round(A(c == "B") - A(c == "I") - bm + im, 2),
             teshik_B_m2=round(hB.area, 1), teshik_I_m2=round(hI.area, 1), haqiqiy_teshik_m2=round(real_area(hB) + real_area(hI), 1))
    return r, b


def main(v1, out, args):
    t0 = time.time()
    ishchi = int(args[args.index("--ishchi") + 1]) if "--ishchi" in args else min(max(1, (os.cpu_count() or 2) - 2), 12)
    print("Qatlamlar:", pyogrio.list_layers(out).tolist())
    for l, _ in pyogrio.list_layers(out):
        print(f"  {l}: {pyogrio.read_info(out, layer=l)['features']} ta")
    info = pyogrio.read_info(out, layer="ekin_yerlar")
    print("CRS:", info["crs"], "| asl 22 ustun bormi:", all(c in info["fields"] for c in ASL22))
    t = pyogrio.read_dataframe(v1, layer="ekin_yerlar", columns=["viloyat", "tuman"], read_geometry=False)
    size = t.groupby(["viloyat", "tuman"]).size()
    with ProcessPoolExecutor(max_workers=ishchi) as ex:
        res = list(ex.map(check, *zip(*[(v1, out, v, tm) for v, tm in sorted(size.index, key=lambda p: -size[p])])))
    R = pd.DataFrame([r for r, _ in res]); T = pd.DataFrame([b for _, b in res]).sort_values(["viloyat", "tuman"])

    def agg(s):
        if s.name == "ruxsatsiz_ozgarish":
            tot = {}
            for d in s:
                for k, v in d.items(): tot[k] = tot.get(k, 0) + v
            return tot or 0
        if s.dtype == bool: return bool(s.all())
        if s.name.endswith("_%"): return round(float(s.max()), 3)
        return int(s.sum())
    V = R.drop(columns="tuman").groupby("viloyat").agg(agg)
    print("\n=== VILOYATLAR ===")
    print(V.T.to_string())
    print("\nbalki muammoli tumanlar (ruxsatsiz o'zgarish / invalid / fid):")
    p = R[(R.ruxsatsiz_ozgarish.map(len) > 0) | (R.invalid > 0) | ~R.fid_toliq | ~R["geom_bir_xil(kesilmaganlar)"]]
    print(p[["viloyat", "tuman", "ruxsatsiz_ozgarish", "invalid", "fid_toliq"]].to_string(index=False) if len(p) else "  yo'q")
    T.to_csv(out.replace(".gpkg", "_tuman_balans.csv"), index=False, encoding="utf-8-sig")
    print("\n=== TUMANLAR: eng katta |farq| va teshiklar ===")
    print(T.reindex(T.farq_ga.abs().sort_values(ascending=False).index).head(10).to_string(index=False))
    print("\nJami:", T[["asl", "yangi", "B_ga", "I_ga", "B_M_ostida", "I_M_ustida", "farq_ga", "teshik_B_m2", "teshik_I_m2",
                        "haqiqiy_teshik_m2"]].sum().round(1).to_dict())
    print(f"Tekshiruv vaqti: {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
