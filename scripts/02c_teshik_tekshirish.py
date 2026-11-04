"""Yangi bo'laklar manba bilan aynan mos tushadimi va mavsum qatlamlarida teshik qoldimi?
python 02c_teshik_tekshirish.py <sinov.gpkg>"""
import sys, numpy as np, pandas as pd, pyogrio, shapely
AEA = "+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=67 +datum=WGS84 +units=m +no_defs"
o = pyogrio.read_dataframe(sys.argv[1], layer="ekin_yerlar")
new = o[o.qoshilgan == 1]; src = o[o.qoshilgan == 0].set_index("fid_asl")
sg = src.geometry.reindex(new.manba_fid.astype("int64")).values

ex = new.aniq_nusxa == 1
# har bir aniq nusxa bo'lak manbaning qaysidir qismi bilan koordinatama-koordinata bir xil bo'lishi kerak
same = np.array([any(shapely.equals_exact(shapely.get_parts(ng)[0], sp, 0) for sp in shapely.get_parts(s))
                 for ng, s in zip(new.geometry.values[ex.values], sg[ex.values])])
print(f"Aniq nusxa bo'laklar: {ex.sum()} ta, koordinatasi manba qismi bilan 100% bir xil: {same.sum()} ta")

# qisman bo'laklar: yangi bo'lak manbaning ichida bo'lishi kerak (chetidan chiqmasin)
pa = ~ex.values
outside = shapely.area(shapely.difference(new.geometry.values[pa], sg[pa]))
print(f"Qisman bo'laklar: {pa.sum()} ta, manbadan tashqariga chiqqan maydon: {outside.sum():.4f} m2")

# teshik: har bir mavsumda to'liq dala yopilganmi (AEA, haqiqiy m2)
g = o.to_crs(AEA)
cls = g.mavsum.map({"Birlamchi ekin": "B", "Ikkilamchi ekin": "I", "Mavsumiy ekin": "M"}).fillna("-").values
geo = g.geometry.values
U = lambda m: shapely.union_all(geo[m])
crop = U(cls != "-")
U_BM, U_IM = U(np.isin(cls, ["B", "M"])), U(np.isin(cls, ["I", "M"]))
for name, cover in (("Birlamchi+Mavsumiy", U_BM), ("Ikkilamchi+Mavsumiy", U_IM)):
    hole = shapely.difference(crop, cover)
    parts = [p for p in shapely.get_parts(hole) if p.area > 0]
    a = np.array([p.area for p in parts]) if parts else np.array([0.0])
    real = sum(p.area for p in parts if p.area >= 200 and not p.buffer(-3, join_style="mitre").is_empty)
    print(f"{name:22s} qatlamida teshik: {len(parts)} ta qism, jami {a.sum():.1f} m2, eng kattasi {a.max():.1f} m2, "
          f"haqiqiy (>=0.02 ga va eni>=6 m): {real:.1f} m2")
