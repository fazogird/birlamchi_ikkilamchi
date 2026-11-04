"""2-bosqich natijasini tekshirish.
python 02b_tekshirish.py <v1.gpkg> <sinov.gpkg> "<tuman>" """
import sys, numpy as np, pandas as pd, pyogrio, shapely
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 100)
v1, out, tm = sys.argv[1], sys.argv[2], sys.argv[3]
FERMER = ["f_name", "f_inn", "f_cad"]; EKIN = ["crop_id", "vh", "yld"]; IK = "Ikkilamchi ekin aniqlanmagan"
SHAPE = ["st_area_sh", "st_perimet", "shape_leng", "Shape_Le_1", "Shape_Area"]   # qayta hisoblanadi
emp = lambda s: s.isna() | s.astype(str).str.strip().isin(["", "None", "nan"])

print("Qatlamlar:", pyogrio.list_layers(out).tolist())
o = pyogrio.read_dataframe(out, layer="ekin_yerlar")
a = pyogrio.read_dataframe(v1, layer="ekin_yerlar", where=f"tuman = '{tm}'")
old = o[o.qoshilgan == 0].sort_values("fid_asl").reset_index(drop=True)
a = a.sort_values("fid_asl").reset_index(drop=True)
print(f"asl qatorlar: v1={len(a)}  natija={len(old)}  yangi={int((o.qoshilgan == 1).sum())}")
print("Asl geometriya bir xil:", bool(shapely.equals_exact(old.geometry.values, a.geometry.values, 1e-6).all()))

# --- asl qatorlarda faqat ruxsat etilgan o'zgarishlar ---
ik = a.turi == IK
bad = {}
for c in [c for c in a.columns if c != "geometry"]:
    same = (old[c] == a[c]) | (old[c].isna() & a[c].isna())
    ch = ~same
    if c in FERMER:                       # faqat bo'shdan to'ldirilgan bo'lishi mumkin
        illegal = ch & ~emp(a[c])
    elif c in EKIN:                       # faqat Ikkilamchi aniqlanmagan da tozalangan bo'lishi mumkin
        illegal = ch & ~(ik & emp(old[c]))
    elif c in SHAPE:                      # qayta hisoblangan: tekshiruv pastda
        illegal = ch & False
    else:
        illegal = ch
    if illegal.any():
        bad[c] = int(illegal.sum())
print("Ruxsat etilmagan o'zgarishlar (bo'sh bo'lishi kerak):", bad or "yo'q")
print("Mavjud fermer qiymati almashtirilganmi:", int(sum(((old[c] != a[c]) & ~emp(a[c])).sum() for c in FERMER)))
print(f"Ikkilamchi aniqlanmagan (asl) {ik.sum()} qator: ekin ustunlari bo'shmi ->",
      {c: bool(emp(old.loc[ik, c]).all()) for c in EKIN}, "| fermer saqlanganmi ->",
      bool((old.loc[ik, "f_inn"].fillna("") == a.loc[ik, "f_inn"].fillna("")).all()))

# --- fermer o'tkazish natijasi ---
got = emp(a.f_inn) & ~emp(old.f_inn)
print(f"\nFermer ma'lumoti o'tkazilgan asl qatorlar: {got.sum()} ta")
print(old[got].groupby(["turi", "mavsum"]).maydon.agg(["size", "sum"]).round(0).to_string())
print("fermer_aralash=1 (turli fermer ustma-ust):", int(o.fermer_aralash.sum()))
print("Fermer ma'lumoti bo'sh qolganlar (mavsum bo'yicha, ga):")
print(o[emp(o.f_inn)].groupby(["qoshilgan", "mavsum"]).maydon.agg(["size", "sum"]).round(0).to_string())

# --- yangi bo'laklar ---
new = o[o.qoshilgan == 1]
nparts = shapely.get_num_geometries(new.geometry.values)
print(f"\nYangi bo'laklar: {len(new)} ta; har biri bitta poligonmi: {bool((nparts == 1).all())} (ko'p qismlilar: {int((nparts > 1).sum())})")
print(pd.crosstab(new.turi, new.mavsum).to_string())
print("Yangi qatorlarda bo'sh bo'lmasligi kerak:", new[["turi", "mavsum", "maydon", "dala_id", "manba_fid", "tuman"]].isna().sum().to_dict())
print("Yangi qatorlarda ekin ustunlari bo'shmi:", {c: bool(emp(new[c]).all()) for c in EKIN})
print("crop_id: aniqlanmagan turlarda bo'shmi:", bool(emp(o.loc[o.turi.str.contains("aniqlanmagan"), "crop_id"]).all()))
print("Invalid geometriya:", int((~o.geometry.is_valid).sum()))
AEA = "+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=67 +datum=WGS84 +units=m +no_defs"
ta = o.to_crs(AEA).geometry.area.values
r = o.Shape_Area.values / ta
print(f"\nShape_Area / haqiqiy maydon: min {r.min():.5f}, max {r.max():.5f} (1 bo'lishi kerak)")
print("st_area_sh == Shape_Area:", bool((o.st_area_sh == o.Shape_Area).all()),
      "| perimetr ustunlari bir xil:", bool(((o.st_perimet == o.shape_leng) & (o.shape_leng == o.Shape_Le_1)).all()),
      "| 0 qiymat:", int((o.Shape_Area <= 0).sum()))
mr = o.maydon.values * 1e4 / ta
print(f"maydon / haqiqiy: yangi qatorlarda min {mr[o.qoshilgan == 1].min():.5f} max {mr[o.qoshilgan == 1].max():.5f}; "
      f"asl qatorlarda |farq|>1%: {int((abs(mr[o.qoshilgan == 0] - 1) > 0.01).sum())} ta")
print("Ustunlar:", [c for c in o.columns if c != "geometry"])
print("Asl 22 ustun hammasi bormi:", all(c in o.columns for c in ["viloyat", "tuman", "region", "district", "maydon", "turi", "yil",
      "globalid_1", "vh", "f_name", "f_inn", "f_cad", "uniqueid", "yld", "crop_id", "yer_turi", "ekin_davri"] + SHAPE))
q = pyogrio.read_info(out, layer="qoshilgan")
print(f"qoshilgan qatlami: {q['features']} ta (ekin_yerlar dagi yangi: {int((o.qoshilgan == 1).sum())})")
