"""
6-modul: mavjud TO'LIQ versiyadan QISQA versiyani qayta yasash (uniqueid O'ZGARMAYDI).

Qachon kerak: to'liq versiya (05 natijasi) allaqachon bor va qisqa versiyani qaytadan olish kerak bo'lsa
(masalan, qisqa versiya qoidasi o'zgarganda) — 05 ni qayta ishlatish uniqueid larni yangilab yuboradi, bu modul esa yo'q.

Qisqa versiya: viloyat | tuman | maydon | turi | yil | uniqueid | season | suv_boshi | suv_oxiri + geometriya
Baliqxovuz va Issiqxona chiqariladi (05 dagi QISQA_CHIQARILADI bilan bir xil).

python 06_qisqa_versiya.py <toliq.gpkg> <qisqa.gpkg>
"""
import os, sys, time, importlib.util
import numpy as np, pyogrio, shapely

# qoidalar 05 dan olinadi — bitta joyda saqlanadi
_spec = importlib.util.spec_from_file_location("m05", os.path.join(os.path.dirname(os.path.abspath(__file__)), "05_uniqueid_eksport.py"))
m05 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(m05)


def main(toliq, qisqa):
    if os.path.exists(qisqa):
        raise SystemExit(f"Chiqish fayli bor, ustiga yozmayman: {qisqa}")
    t0 = time.time()
    y = pyogrio.read_dataframe(toliq, layer="ekin_yerlar")
    if "season" not in y.columns:
        y = y.rename(columns={"mavsum": "season"})
    miss = [c for c in m05.QISQA if c not in y.columns]
    if miss:
        raise SystemExit(f"To'liq versiyada ustun yo'q: {miss} (bu 05 natijasimi?)")
    if not y.uniqueid.is_unique or y.uniqueid.isna().any():
        raise SystemExit("To'liq versiyada uniqueid takrorlanadi yoki bo'sh — avval 05 ni ishlating")
    s = y[~y.turi.isin(m05.QISQA_CHIQARILADI)][m05.QISQA + ["geometry"]]
    n_multi = int((shapely.get_num_geometries(s.geometry.values) > 1).sum())
    pyogrio.write_dataframe(s, qisqa, layer="ekin_yerlar", driver="GPKG", promote_to_multi=n_multi > 0,
                            **({} if n_multi else {"geometry_type": "Polygon"}))
    print(f"To'liq: {len(y)} qator -> qisqa: {len(s)} qator ({', '.join(m05.QISQA_CHIQARILADI)} chiqarildi: {len(y) - len(s)} ta)")
    print("Qisqada qolgan turlar:", sorted(s.turi.dropna().unique().tolist()))
    print(f"uniqueid to'liq versiya bilan bir xil (o'zgarmadi): {bool(s.uniqueid.isin(y.uniqueid).all())}, takrorsiz: {s.uniqueid.is_unique}")
    if n_multi:
        print(f"Ogohlantirish: to'liq versiyada {n_multi} ta multipart poligon bor (eski 05 bilan olingan bo'lishi mumkin)")
    print(f"Qisqa: {qisqa}  (ustunlar: {m05.QISQA})  | vaqt {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
