"""Qishloq jamoasi tekshirib tuzatishi uchun xatolar / o'zgarishlar ro'yxati (Excel).
python 04_xatolar_excel.py <v1.gpkg> <yakuniy.gpkg> <chiqish.xlsx> [tuman_balans.csv]"""
import os, sys, numpy as np, pandas as pd, pyogrio, shapely
from concurrent.futures import ProcessPoolExecutor
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

AEA = "+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=67 +datum=WGS84 +units=m +no_defs"
# viloyatlar ro'yxati kirish faylidan olinadi (qattiq yozilmaydi)
emp = lambda s: s.isna() | s.astype(str).str.strip().isin(["", "None", "nan"])


def cross_tuman(v1, v):
    """Bir viloyat ichida turli tumandagi poligonlar ustma-ust tushgan joylar (> 100 m2)."""
    g = pyogrio.read_dataframe(v1, layer="ekin_yerlar", where=f"viloyat = '{v.replace(chr(39), chr(39)*2)}'",
                               columns=["fid_asl", "tuman", "turi", "mavsum"]).to_crs(AEA)
    inv = ~g.geometry.is_valid
    if inv.any():
        g.loc[inv, "geometry"] = shapely.make_valid(g.geometry.values[inv.values])
    geo = g.geometry.values
    li, ri = shapely.STRtree(geo).query(geo, predicate="intersects")
    k = (li < ri) & (g.tuman.values[li] != g.tuman.values[ri]); li, ri = li[k], ri[k]
    ia = shapely.area(shapely.intersection(geo[li], geo[ri]))
    k = ia > 100
    return [dict(viloyat=v, tuman_1=g.tuman[i], fid_1=g.fid_asl[i], turi_1=g.turi[i], mavsum_1=g.mavsum[i],
                 tuman_2=g.tuman[j], fid_2=g.fid_asl[j], turi_2=g.turi[j], mavsum_2=g.mavsum[j], ustma_ust_ga=round(a / 1e4, 3))
            for i, j, a in zip(li[k], ri[k], ia[k])]


def main():
    v1, out, xlsx = sys.argv[1], sys.argv[2], sys.argv[3]
    bal_csv = sys.argv[4] if len(sys.argv) > 4 else None
    cols = ["fid_asl", "viloyat", "tuman", "turi", "mavsum", "ekin_davri", "maydon", "f_name", "f_inn", "f_cad", "qoshilgan",
            "dala_id", "ziddiyat", "fermer_manba_fid", "fermer_aralash", "geom_tuzatildi", "kesildi", "manba_fid", "manba_turi"]
    Y = pyogrio.read_dataframe(out, layer="ekin_yerlar", columns=cols, read_geometry=False)
    A = pyogrio.read_dataframe(v1, layer="ekin_yerlar", columns=["fid_asl", "maydon", "f_name", "f_inn"], read_geometry=False)
    T = pyogrio.read_dataframe(out, layer="tashlangan", read_geometry=False)         if "tashlangan" in [l for l, _ in pyogrio.list_layers(out)] else         pd.DataFrame(columns=["viloyat", "tuman", "manba_fid", "manba_turi", "sabab", "maydon_m2"])
    old = Y[Y.qoshilgan == 0].merge(A.rename(columns={"maydon": "maydon_asl", "f_name": "f_name_asl", "f_inn": "f_inn_asl"}), on="fid_asl", how="left")
    sheets = {}

    # 1. Paxta ustidagi ikkilamchi
    p = T[T.sabab.astype(str).str.startswith("Ikkilamchi")].copy()
    p = p.merge(A.rename(columns={"fid_asl": "manba_fid"})[["manba_fid", "f_name", "f_inn"]], on="manba_fid", how="left")
    p["maydon_ga"] = (p.maydon_m2 / 1e4).round(3)
    sheets["Paxta_ustida_ikkilamchi"] = p[["viloyat", "tuman", "manba_fid", "manba_turi", "sabab", "maydon_ga", "f_name", "f_inn"]] \
        .rename(columns={"manba_fid": "fid_asl", "manba_turi": "turi", "maydon_ga": "kesilgan_maydon_ga"})

    # 2. Tuman chegarasi: turli tumandagi poligonlar ustma-ust (> 100 m2) — viloyatlar parallel
    VIL = sorted(Y.viloyat.dropna().unique().tolist())
    with ProcessPoolExecutor(max_workers=max(1, min(len(VIL), 12))) as ex:
        rows = [r for part in ex.map(cross_tuman, [v1] * len(VIL), VIL) for r in part]

    sheets["Tuman_chegarasi"] = pd.DataFrame(rows)

    # 3. Fermer aralash
    fa = Y[Y.fermer_aralash == 1]
    sheets["Fermer_aralash"] = fa[["viloyat", "tuman", "fid_asl", "qoshilgan", "manba_fid", "turi", "mavsum", "maydon", "f_name", "f_inn",
                                   "fermer_manba_fid", "dala_id"]].round({"maydon": 3})

    # 4. Fermer ma'lumoti o'tkazilganlar (asl qatorlar)
    ft = old[emp(old.f_inn_asl) & ~emp(old.f_inn)]
    sheets["Fermer_otkazildi"] = ft[["viloyat", "tuman", "fid_asl", "turi", "mavsum", "maydon", "f_name", "f_inn", "f_cad",
                                     "fermer_manba_fid", "fermer_aralash"]].round({"maydon": 3})

    # 5. Maydon qayta hisoblangan (> 1% farq)
    old["farq_%"] = ((old.maydon_asl - old.maydon) / old.maydon * 100).round(2)
    mf = old[old["farq_%"].abs() > 1]
    sheets["Maydon_tuzatildi"] = mf[["viloyat", "tuman", "fid_asl", "turi", "maydon_asl", "maydon", "farq_%"]] \
        .rename(columns={"maydon_asl": "maydon_eski_ga", "maydon": "maydon_yangi_ga"}).round({"maydon_eski_ga": 4, "maydon_yangi_ga": 4})

    # 6. Geometriya tuzatilgan / kesilgan
    gt = old[(old.geom_tuzatildi == 1) | (old.kesildi == 1)].copy()
    gt["nima_qilindi"] = np.where(gt.kesildi == 1, "Paxta ustidagi qismi kesildi", "buzuq (invalid) geometriya make_valid bilan tuzatildi")
    sheets["Geometriya_ozgardi"] = gt[["viloyat", "tuman", "fid_asl", "turi", "mavsum", "maydon", "nima_qilindi"]].round({"maydon": 3})

    # 7. Ziddiyat
    zd = Y[~emp(Y.ziddiyat)]
    sheets["Ziddiyat"] = zd[["viloyat", "tuman", "fid_asl", "turi", "mavsum", "maydon", "ziddiyat", "dala_id"]].round({"maydon": 3})

    # 8. Fermer ma'lumoti yo'q — xulosa
    fy = Y[emp(Y.f_inn) & Y.mavsum.notna()]
    sheets["Fermer_yoq_xulosa"] = fy.assign(yangi=np.where(fy.qoshilgan == 1, "yangi qo'shilgan", "asl")) \
        .groupby(["viloyat", "tuman", "mavsum", "yangi"]).agg(soni=("maydon", "size"), maydon_ga=("maydon", "sum")).round(1).reset_index()

    # 9. Tuman balansi
    if bal_csv and os.path.exists(bal_csv):
        sheets["Tuman_balans"] = pd.read_csv(bal_csv)

    # Izoh
    izoh = pd.DataFrame([
        ("Paxta_ustida_ikkilamchi", "Birlamchidan (Ozuqa/Bug'doy) keyin Paxta ekilgan joyda turgan 'Ikkilamchi ekin aniqlanmagan'. Paxta ustidagi qismi kesildi yoki kontur butunlay olib tashlandi (tashlangan qatlamida bor)."),
        ("Tuman_chegarasi", "Bir tumandagi poligon qo'shni tumandagi poligon ustida turibdi. Hisobda to'g'ri hisobga olingan; tuman nomi to'g'riligini tekshiring."),
        ("Fermer_aralash", "Poligon ikki xil fermer (f_inn) dalasi ustiga tushadi; fermer ma'lumoti eng ko'p ustma-ust tushgan daladan olingan — tekshiring."),
        ("Fermer_otkazildi", "Bo'sh bo'lgan f_name/f_inn/f_cad ustma-ust turgan katta daladan (fermer_manba_fid) o'tkazilgan asl poligonlar."),
        ("Maydon_tuzatildi", "maydon ustuni geometriyadan 1% dan ko'p farq qilgan; geometriyadan (geodezik) qayta hisoblandi."),
        ("Geometriya_ozgardi", "Geometriyasi o'zgargan asl poligonlar: buzuq geometriya tuzatilgan yoki Paxta ustidagi qismi kesilgan."),
        ("Ziddiyat", "Bir mavsum ichida ustma-ust yoki Ikkilamchi Mavsumiy ustida turgan poligonlar (> 100 m2)."),
        ("Fermer_yoq_xulosa", "Fermer ma'lumoti (f_inn) yo'q poligonlar soni va maydoni — tuman va mavsum bo'yicha (asl faylda ham yo'q)."),
        ("Tuman_balans", "Har tuman: Birlamchi, Ikkilamchi maydoni, Mavsumiy bilan yopilgan qism, balans farqi va mavsum qatlamlaridagi teshiklar."),
    ], columns=["varaq", "nima"])
    izoh["qatorlar_soni"] = [len(sheets.get(s, [])) for s in izoh.varaq]

    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        izoh.to_excel(w, sheet_name="Izoh", index=False)
        for name, df in sheets.items():
            df.to_excel(w, sheet_name=name[:31], index=False)
        for ws in w.book.worksheets:
            for c in ws[1]:
                c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2F5597")
                c.alignment = Alignment(wrap_text=True, vertical="center")
            ws.freeze_panes = "A2"
            if ws.max_row > 1:
                ws.auto_filter.ref = ws.dimensions
            for k, col in enumerate(ws.iter_cols(min_row=1, max_row=min(ws.max_row, 200)), 1):
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
                ws.column_dimensions[get_column_letter(k)].width = min(max(10, width + 2), 60 if ws.title != "Izoh" else 120)
    print(izoh.to_string(index=False))
    print("Yozildi:", xlsx)


if __name__ == "__main__":
    main()
