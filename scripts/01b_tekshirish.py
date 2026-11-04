"""1-bosqich natijasini tekshirish: soni, validlik, mavsum, apostrof.
python 01b_tekshirish.py <asl.shp> <natija.gpkg>"""
import sys, pandas as pd, pyogrio, shapely
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 100)
src, dst = sys.argv[1], sys.argv[2]

a = pyogrio.read_info(src, encoding="utf-8"); b = pyogrio.read_info(dst, layer="ekin_yerlar")
print("Soni: asl", a["features"], "| natija", b["features"], "| CRS", b["crs"], "|", b["geometry_type"])

g = pyogrio.read_dataframe(dst, layer="ekin_yerlar", columns=["fid_asl", "viloyat", "turi", "ekin_davri", "mavsum", "maydon", "vh", "tuman", "geom_tuzatildi"])
print("fid_asl takrorlanmaydi:", g.fid_asl.is_unique, "| min/max", g.fid_asl.min(), g.fid_asl.max())
print("Invalid geometriya qoldi:", int((~g.geometry.is_valid).sum()), "| bo'sh geometriya:", int(g.geometry.isna().sum() + g.geometry.is_empty.sum()))
print("Tuzatilgan geometriyalar:", int(g.geom_tuzatildi.sum()))

bad = "‘’ʻʼ`´"
for c in ["turi", "vh", "tuman", "viloyat", "ekin_davri"]:
    n = g[c].dropna().astype(str).str.contains(f"[{bad}]").sum()
    print(f"Noto'g'ri apostrof qoldi [{c}]: {n}")

print("\n=== turi x mavsum (soni) ===")
print(pd.crosstab(g.turi, g.mavsum.fillna("— (bo'sh)"), margins=True).to_string())
print("\n=== mavsum x asl ekin_davri ===")
print(pd.crosstab(g.mavsum.fillna("— (bo'sh)"), g.ekin_davri.fillna("NA"), margins=True).to_string())
print("\n=== mavsum bo'yicha maydon (ga) ===")
print(g.groupby(g.mavsum.fillna("— (bo'sh)")).maydon.sum().round(0).to_string())
print("\nvh qiymatlari:", g.vh.dropna().unique().tolist())
