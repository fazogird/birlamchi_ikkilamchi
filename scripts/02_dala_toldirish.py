"""
2-3 bosqich: yetim mavsumlarni to'ldirish, dala_id, o'zgarmas atributlarni o'tkazish, Shape ustunlarini tuzatish.

Qoidalar va ustunlar ma'nosi: QOIDALAR.md

Har bir tuman alohida ishlanadi, lekin qo'shni tumanlarning chegaradagi poligonlari KONTEKST sifatida o'qiladi
(yopuvchi va fermer manbasi bo'la oladi, natijaga yozilmaydi) — tuman chegarasida xato "yetim" chiqmasligi uchun.

Chiqish GeoPackage (EPSG:3857), 3 qatlam:
  ekin_yerlar  — barcha asl poligonlar (barcha 22 asl ustun saqlanadi) + yangi qo'shilgan bo'laklar
  qoshilgan    — faqat yangi qo'shilgan bo'laklar (ekin_yerlar dagi bilan bir xil ustunlar)
  tashlangan   — yaratilmagan chiziq-xatosi qoldiqlari (tekshirish uchun)

Tumanlar parallel (bir nechta CPU yadrosida) hisoblanadi, natija faylga tuman nomi tartibida yoziladi.

python 02_dala_toldirish.py <v1.gpkg> <chiqish.gpkg> --hammasi [--ishchi 12] [--ichki-tekshiruv]
python 02_dala_toldirish.py <v1.gpkg> <chiqish.gpkg> "<tuman>" ["<tuman 2>" ...]
  --ishchi N          parallel jarayonlar soni (standart: yadrolar soni - 2, ko'pi bilan 12)
  --ichki-tekshiruv   balans va yopilmagan qismlarni shu skript ichida ham hisoblash (sekinroq;
                      odatda 03_yakuniy_tekshirish.py buni qiladi)
"""
import os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np, pandas as pd, geopandas as gpd, pyogrio, shapely
from pyproj import Geod
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

AEA = "+proj=aea +lat_1=38 +lat_2=42 +lat_0=40 +lon_0=67 +datum=WGS84 +units=m +no_defs"
SLIVER_M = 3.0          # eni 2*3 = 6 m dan tor qoldiq = chiziq xatosi (faqat bo'lak yaratish-yaratmaslikni hal qiladi)
MIN_M2 = 200.0          # 0.02 ga dan kichik qoldiq = chiziq xatosi
MIN_OVERLAP_M2 = 100.0  # dala_id va fermer o'tkazish uchun ustma-ustlik chegarasi
ARALASH_ULUSH = 0.10    # ikkinchi fermer poligonning >10% ini egallasa -> fermer_aralash = 1
MAYDON_QAYTA = True     # True: asl qatorlarda ham `maydon` geometriyadan (geodezik, ga) qayta hisoblanadi (qaror 2026-11-04)
CLS = {"Birlamchi ekin": "B", "Ikkilamchi ekin": "I", "Mavsumiy ekin": "M"}
NEW = {"B": ("Birlamchi ekin aniqlanmagan", "Birlamchi ekin"), "I": ("Ikkilamchi ekin aniqlanmagan", "Ikkilamchi ekin")}
COPY_COLS = ["viloyat", "tuman", "region", "district", "yil", "f_name", "f_inn", "f_cad"]
FERMER = ["f_name", "f_inn", "f_cad"]
EKIN_COLS = ["crop_id", "vh", "yld"]
IK_ASL = "Ikkilamchi ekin aniqlanmagan"
AREA_COLS = ["st_area_sh", "Shape_Area"]                 # haqiqiy maydon, m2
LEN_COLS = ["st_perimet", "shape_leng", "Shape_Le_1"]    # haqiqiy perimetr, m
GEOD = Geod(ellps="WGS84")


def _safe(op, *args):
    """GEOS topologiya xatosida 1 sm aniqlik to'riga keltirib qayta urinadi (faqat xato bergan holatlarda)."""
    try:
        return op(*args)
    except shapely.errors.GEOSException:
        fixed = [shapely.make_valid(shapely.set_precision(a, 0.01)) for a in args]
        return op(*fixed)


def inter(a, b): return _safe(shapely.intersection, a, b)
def diff(a, b): return _safe(shapely.difference, a, b)
def uall(arr):
    try:
        return shapely.union_all(arr)
    except shapely.errors.GEOSException:
        return shapely.union_all(shapely.make_valid(shapely.set_precision(np.asarray(arr), 0.01)))


def empty(v):
    return v is None or (isinstance(v, float) and np.isnan(v)) or str(v).strip() in ("", "None", "nan")


def is_real(part):
    """Qism haqiqiy maydonmi (chiziq xatosi emasmi)? Geometriyani O'ZGARTIRMAYDI, faqat tekshiradi."""
    return part.area >= MIN_M2 and not part.buffer(-SLIVER_M, join_style="mitre").is_empty


def polys(geom):
    return [p for p in shapely.get_parts(geom) if p.geom_type == "Polygon" and not p.is_empty] if geom is not None else []


def geodesic(geoms_4326):
    """Ellipsoiddagi haqiqiy maydon (m2) va perimetr (m)."""
    a, p = np.empty(len(geoms_4326)), np.empty(len(geoms_4326))
    for k, gm in enumerate(geoms_4326):
        ar, pr = GEOD.geometry_area_perimeter(gm)
        a[k], p[k] = abs(ar), pr
    return a, p


def fill(g, tree, src_cls, block_cls, tgt):
    """Faqat maqsadli tuman poligonlari uchun: [(idx, geom, aniq_nusxa)], [(idx, tashlangan_geom)]"""
    geoms, cls = g.geometry.values, g["cls"].values
    rows, dropped = [], []
    for i in np.where((cls == src_cls) & tgt)[0]:
        cand = tree.query(geoms[i], predicate="intersects")
        cand = cand[np.isin(cls[cand], block_cls)]
        if len(cand):
            blk = uall(geoms[cand])
            if shapely.area(inter(geoms[i], blk)) < 1e-6:
                rows.append((i, geoms[i], True)); continue
            rest = diff(geoms[i], blk)
        else:
            rows.append((i, geoms[i], True)); continue
        parts = polys(rest)
        if not parts:
            continue
        if any(is_real(p) for p in parts):
            rows.append((i, uall(parts), False))
        else:
            dropped.append((i, uall(parts)))
    return rows, dropped


def neighbour_type(g, tree, geom, want_cls):
    zone = geom.buffer(5)
    cand = tree.query(zone, predicate="intersects")
    cand = cand[g["cls"].values[cand] == want_cls]
    if len(cand):
        cand = cand[np.array(["aniqlanmagan" not in str(t) for t in g["turi"].values[cand]], dtype=bool)]
    if not len(cand):
        return None
    sh = [inter(zone, g.geometry.values[c]).area for c in cand]
    return g["turi"].values[cand[int(np.argmax(sh))]]


def uncovered(allg, allc, idx, block, tree):
    tot = real = 0.0
    for i in idx:
        c = tree.query(allg[i], predicate="intersects"); c = c[np.isin(allc[c], block)]
        r = diff(allg[i], uall(allg[c])) if len(c) else allg[i]
        for p in polys(r):
            tot += p.area
            real += p.area if is_real(p) else 0
    return round(tot / 1e4, 2), round(real / 1e4, 2)


def read_with_context(src, viloyat, tuman):
    q = lambda s: s.replace("'", "''")
    t = pyogrio.read_dataframe(src, layer="ekin_yerlar", where=f"viloyat = '{q(viloyat)}' AND tuman = '{q(tuman)}'")
    if t.empty:
        raise SystemExit(f"Tuman topilmadi: {viloyat} / {tuman}")
    xmin, ymin, xmax, ymax = t.total_bounds
    c = pyogrio.read_dataframe(src, layer="ekin_yerlar", bbox=(xmin - 50, ymin - 50, xmax + 50, ymax + 50))
    c = c[~((c.viloyat == viloyat) & (c.tuman == tuman))]
    c = c[c.intersects(uall(t.geometry.values).buffer(50))] if len(c) else c
    t["_tgt"] = True; c["_tgt"] = False
    return gpd.GeoDataFrame(pd.concat([t, c], ignore_index=True), geometry="geometry", crs=t.crs)


def process(src, viloyat, tuman, ichki=False):
    t0 = time.time()
    g3857 = read_with_context(src, viloyat, tuman)
    tgt = g3857["_tgt"].values.astype(bool)
    g = g3857.to_crs(AEA)
    inv = ~g.geometry.is_valid                       # proyeksiyadan keyin yaroqsiz bo'lib qolganlar (hisob uchun)
    if inv.any():
        g.loc[inv, "geometry"] = [uall(polys(shapely.make_valid(x))) for x in g.geometry.values[inv.values]]
    g["cls"] = g["mavsum"].map(CLS).fillna("-")

    # --- 0. Ikkilamchi Mavsumiy (Paxta) ustida: Birlamchidan keyin Paxta ekilgan -> ikkilamchi bo'lmaydi.
    #        Ikkilamchining Mavsumiy ustidagi haqiqiy qismi kesiladi; qolgani haqiqiy bo'lmasa butun kontur olib tashlanadi.
    g3857["kesildi"] = 0; g["kesildi"] = 0
    cut_recs, drop_rows = [], []
    t0tree = shapely.STRtree(g.geometry.values)
    gv, cv = g.geometry.values, g.cls.values
    for i in np.where((cv == "I") & tgt)[0]:
        cand = t0tree.query(gv[i], predicate="intersects"); cand = cand[cv[cand] == "M"]
        if not len(cand):
            continue
        xp = [p for p in polys(inter(gv[i], uall(gv[cand]))) if is_real(p)]
        if not xp:
            continue                                  # faqat chegara tegishi — tegilmaydi
        cut = uall(xp)
        m_turi = g.turi.values[cand[np.argmax([inter(gv[i], gv[c]).area for c in cand])]]
        rp = polys(diff(gv[i], cut))
        whole = not any(is_real(p) for p in rp)
        cut_recs.append(dict(manba_fid=int(g.fid_asl.values[i]), manba_turi=g.turi.values[i], yetishmagan=None,
                             sabab=f"Ikkilamchi {m_turi} (Mavsumiy) ustida — " + ("butun kontur olib tashlandi" if whole else "ustidagi qismi kesildi"),
                             maydon_m2=round((gv[i] if whole else cut).area, 1), viloyat=viloyat, tuman=tuman,
                             geometry=gv[i] if whole else cut))
        if whole:
            drop_rows.append(i)
        else:
            newg = uall(rp)
            g.iat[i, g.columns.get_loc("geometry")] = newg
            g.iat[i, g.columns.get_loc("kesildi")] = 1
            g3857.iat[i, g3857.columns.get_loc("geometry")] = gpd.GeoSeries([newg], crs=AEA).to_crs(g3857.crs).values[0]
            g3857.iat[i, g3857.columns.get_loc("kesildi")] = 1
    if drop_rows:
        keep = np.ones(len(g), dtype=bool); keep[drop_rows] = False
        g = g[keep].reset_index(drop=True); g3857 = g3857[keep].reset_index(drop=True); tgt = tgt[keep]
    cut_df = gpd.GeoDataFrame(cut_recs, geometry="geometry", crs=AEA) if cut_recs else None

    tree = shapely.STRtree(g.geometry.values)
    n_old = len(g)

    # --- 1. to'ldirish (faqat maqsadli tuman manbalari; yopuvchi = hammasi, kontekst ham) ---
    newB, dropB = fill(g, tree, "I", ["B", "M"], tgt)
    newI, dropI = fill(g, tree, "B", ["I", "M"], tgt)
    recs = []
    for kind, rows in (("B", newB), ("I", newI)):
        turi, mavsum = NEW[kind]
        for i, p, exact in rows:
            r = {c: g[c].values[i] for c in COPY_COLS}
            r.update(turi=turi, mavsum=mavsum, ekin_davri=None, qoshilgan=1,
                     manba_fid=float(g["fid_asl"].values[i]), manba_turi=g["turi"].values[i],
                     aniq_nusxa=int(exact), cls=kind, src_idx=i, geometry=p)
            recs.append(r)
    n_rec = len(recs)
    if recs:
        new = gpd.GeoDataFrame(recs, geometry="geometry", crs=AEA).explode(index_parts=True)
        new["part_no"] = new.index.get_level_values(1)
        new = new.reset_index(drop=True)
        new = new[new.geometry.geom_type == "Polygon"].reset_index(drop=True)
        # ajratilgandan keyin chiziq xatosi bo'lib qolgan mayda/ingichka qismlar -> tashlangan
        real = np.array([is_real(p) for p in new.geometry.values], dtype=bool)
        for i, p, kd in zip(new.src_idx.values[~real], new.geometry.values[~real], new.cls.values[~real]):
            (dropB if kd == "B" else dropI).append((int(i), p))
        new = new[real].reset_index(drop=True)
        new["maydon"] = new.geometry.area / 1e4
        new["qoshni_turi"] = [neighbour_type(g, tree, p, k) for p, k in zip(new.geometry.values, new.cls.values)]
    else:
        new = gpd.GeoDataFrame({"cls": pd.Series(dtype=object), "src_idx": pd.Series(dtype=int),
                                "part_no": pd.Series(dtype=int), "geometry": []}, geometry="geometry", crs=AEA)
    drops = [(i, p, "Birlamchi") for i, p in dropB] + [(i, p, "Ikkilamchi") for i, p in dropI]
    tash = gpd.GeoDataFrame({"manba_fid": [int(g["fid_asl"].values[i]) for i, _, _ in drops],
                             "manba_turi": [g["turi"].values[i] for i, _, _ in drops],
                             "yetishmagan": [k for _, _, k in drops],
                             "sabab": "chiziq xatosi — yangi bo'lak yaratilmadi",
                             "maydon_m2": [round(p.area, 1) for _, p, _ in drops],
                             "viloyat": viloyat, "tuman": tuman},
                            geometry=[p for _, p, _ in drops], crs=AEA)
    if cut_df is not None:
        tash = gpd.GeoDataFrame(pd.concat([cut_df, tash], ignore_index=True), geometry="geometry", crs=AEA)

    # --- ziddiyat ---
    li, ri = tree.query(g.geometry.values, predicate="intersects")
    m = li < ri
    li, ri = li[m], ri[m]
    ia = shapely.area(inter(g.geometry.values[li], g.geometry.values[ri]))
    ok = ia > MIN_OVERLAP_M2
    li, ri, ia = li[ok], ri[ok], ia[ok]
    pair = np.array(["".join(sorted((x, y))) for x, y in zip(g.cls.values[li], g.cls.values[ri])], dtype=object)
    zid_lbl = {"IM": "Ikkilamchi Mavsumiy ustida", "MM": "Mavsumiy ustma-ust", "BB": "Birlamchi ustma-ust", "II": "Ikkilamchi ustma-ust"}
    zid = np.full(n_old, None, dtype=object)
    zid_stats = {}
    for k, lbl in zid_lbl.items():
        s = pair == k
        if s.any():
            idx = np.concatenate([li[s], ri[s]])
            zid[idx] = lbl
            sk = s & (tgt[li] | tgt[ri])
            if sk.any():
                zid_stats[lbl] = (int(sk.sum()), round(ia[sk].sum() / 1e4, 1))

    # --- dala_id ---
    allg = np.concatenate([g.geometry.values, new.geometry.values])
    allc = np.concatenate([g.cls.values, new.cls.values])
    all_tgt = np.concatenate([tgt, np.ones(len(new), dtype=bool)])
    n = len(allg)
    t2 = shapely.STRtree(allg)
    a_, b_ = t2.query(allg, predicate="intersects")
    k = a_ < b_
    a_, b_ = a_[k], b_[k]
    ia_all = shapely.area(inter(allg[a_], allg[b_]))
    ov = ia_all > MIN_OVERLAP_M2
    a_, b_, ia_all = a_[ov], b_[ov], ia_all[ov]
    _, lab = connected_components(coo_matrix((np.ones(len(a_)), (a_, b_)), shape=(n, n)), directed=False)
    pref = str(g.loc[tgt, "district"].values[0]).replace(" ", "_")[:20]
    dala_id = np.array([f"{pref}_{x:06d}" for x in lab], dtype=object)

    # --- 3. fermer ma'lumotini ustma-ust turgan asl poligondan o'tkazish ---
    finn = np.concatenate([g.f_inn.values, new.f_inn.values]) if len(new) else g.f_inn.values
    has_f = np.array([not empty(v) for v in finn])
    donor_ok = has_f.copy(); donor_ok[n_old:] = False
    areas = shapely.area(allg)
    tg = np.concatenate([a_, b_]); dn = np.concatenate([b_, a_]); w = np.concatenate([ia_all, ia_all])
    s = (~has_f[tg]) & donor_ok[dn] & all_tgt[tg]
    T = pd.DataFrame({"t": tg[s], "d": dn[s], "ia": w[s], "inn": finn[dn[s]]})
    fer_src = np.full(n, np.nan); aralash = np.zeros(n, dtype="int8")
    if len(T):
        best = T.sort_values("ia", ascending=False).drop_duplicates("t")
        sig = T[T.ia > ARALASH_ULUSH * areas[T.t.values]]
        n_inn = sig.groupby("t").inn.nunique()
        aralash[n_inn[n_inn > 1].index.values] = 1
        for t, d in zip(best.t.values, best.d.values):
            for c in FERMER:
                v = g[c].values[d]
                if t < n_old:
                    g.iat[t, g.columns.get_loc(c)] = v
                else:
                    new.iat[t - n_old, new.columns.get_loc(c)] = v
            fer_src[t] = g["fid_asl"].values[d]
    turi_all = np.concatenate([g.turi.values, new.turi.values]) if len(new) else g.turi.values
    fer_stat = pd.Series(turi_all)[~np.isnan(fer_src) & all_tgt].value_counts().to_dict()

    # --- balans (faqat maqsadli tuman + yangi) ---
    area_t = lambda c: areas[(allc == c) & all_tgt].sum() / 1e4
    B_old = areas[:n_old][(g.cls.values == "B") & tgt].sum() / 1e4
    I_old = areas[:n_old][(g.cls.values == "I") & tgt].sum() / 1e4
    BM, uI, uB = np.nan, "-", "-"
    if ichki:                                      # ixtiyoriy: 03_yakuniy_tekshirish.py ham shuni tekshiradi
        BM = 0.0
        for i in np.where((allc == "B") & all_tgt)[0]:
            c = t2.query(allg[i], predicate="intersects"); c = c[allc[c] == "M"]
            if len(c):
                BM += inter(allg[i], uall(allg[c])).area
        BM /= 1e4
        uI = uncovered(allg, allc, np.where((allc == "I") & all_tgt)[0], ["B", "M"], t2)
        uB = uncovered(allg, allc, np.where((allc == "B") & all_tgt)[0], ["I", "M"], t2)
    ik_mask = (g.turi.values == IK_ASL) & tgt
    rep = dict(viloyat=viloyat, tuman=tuman, n_asl=int(tgt.sum()), n_kontekst=int((~tgt).sum()),
               paxta_ustidagi_ikkilamchi=f"kesildi {int(g.kesildi.values[tgt].sum())}, olib tashlandi {len(drop_rows)}, "
                                         f"{(cut_df.geometry.area.sum() / 1e4 if cut_df is not None else 0):.2f} ga",
               yangi=f"{n_rec} yozuv -> {len(new)} bo'lak (B {int((new.cls == 'B').sum())}, I {int((new.cls == 'I').sum())}), "
                     f"aniq nusxa {int((new.aniq_nusxa == 1).sum()) if len(new) else 0}",
               B=f"{B_old:.0f} -> {area_t('B'):.0f} ga", I=f"{I_old:.0f} -> {area_t('I'):.0f} ga",
               B_ustida_M=round(BM) if ichki else "-", farq=round(area_t("B") - area_t("I") - BM, 2) if ichki else "-",
               yopilmagan_I=uI, yopilmagan_B=uB, tashlangan=f"{len(tash)} ta, {tash.geometry.area.sum()/1e4:.2f} ga",
               fermer_otkazildi=fer_stat, fermer_aralash=int(aralash[all_tgt].sum()),
               ikk_aniqlanmagan_tozalandi=int(ik_mask.sum()), ziddiyat=zid_stats, soniya=round(time.time() - t0))

    # --- chiqish (EPSG:3857), faqat maqsadli tuman ---
    out_old = g3857[tgt].drop(columns="_tgt").copy()
    for c in FERMER:
        out_old[c] = g[c].values[tgt]
    out_old.loc[ik_mask[tgt], EKIN_COLS] = None
    out_old["qoshilgan"] = 0
    out_old["dala_id"] = dala_id[:n_old][tgt]
    out_old["ziddiyat"] = zid[tgt]
    out_old["fermer_manba_fid"] = fer_src[:n_old][tgt]
    out_old["fermer_aralash"] = aralash[:n_old][tgt]
    out_old["manba_fid"] = np.nan
    for c in ("manba_turi", "qoshni_turi"):
        out_old[c] = pd.Series([None] * len(out_old), dtype=object, index=out_old.index)
    out_old["aniq_nusxa"] = np.nan
    out_new = None
    if len(new):
        new["dala_id"] = dala_id[n_old:]
        new["fermer_manba_fid"] = fer_src[n_old:]; new["fermer_aralash"] = aralash[n_old:]
        out_new = new.drop(columns=["cls"]).to_crs(g3857.crs)
        geo = out_new.geometry.values.copy()
        for j in np.where(out_new.aniq_nusxa.values == 1)[0]:
            geo[j] = shapely.get_parts(g3857.geometry.values[int(out_new.src_idx.values[j])])[int(out_new.part_no.values[j])]
        out_new = out_new.set_geometry(gpd.GeoSeries(geo, crs=g3857.crs, index=out_new.index)).drop(columns=["src_idx", "part_no"])
        out_new = out_new.reindex(columns=out_old.columns)
        allrows = gpd.GeoDataFrame(pd.concat([out_old, out_new], ignore_index=True), geometry="geometry", crs=g3857.crs)
    else:
        allrows = out_old.reset_index(drop=True)

    # --- 3857 ga qaytarilgandan keyin o'z-o'zini kesib qolgan yangi/kesilgan geometriyalarni tuzatish ---
    fixm = (~allrows.geometry.is_valid).values & ((allrows.qoshilgan.values == 1) | (allrows.kesildi.fillna(0).values == 1))
    gcol = allrows.columns.get_loc("geometry")
    for j in np.where(fixm)[0]:
        ps = polys(shapely.make_valid(allrows.geometry.values[j]))
        # yangi bo'lak bitta Polygon qolishi kerak: o'z-o'zini kesishdan chiqqan mayda bo'laklar tashlanadi
        allrows.iat[j, gcol] = max(ps, key=lambda p: p.area) if allrows.qoshilgan.values[j] == 1 else uall(ps)
    rep["chiqishda_tuzatildi"] = int(fixm.sum())

    # --- Shape ustunlari: haqiqiy (geodezik) maydon m2 va perimetr m ---
    ar, pr = geodesic(allrows.geometry.to_crs(4326).values)
    for c in AREA_COLS:
        allrows[c] = np.round(ar, 2)
    for c in LEN_COLS:
        allrows[c] = np.round(pr, 2)
    yangi = allrows.qoshilgan.values == 1
    allrows.loc[yangi, "maydon"] = ar[yangi] / 1e4
    if MAYDON_QAYTA:
        allrows["maydon"] = ar / 1e4
    for c in ("fid_asl", "manba_fid", "aniq_nusxa", "fermer_manba_fid"):
        allrows[c] = pd.to_numeric(allrows[c]).round().astype("Int64")
    for c in ("qoshilgan", "fermer_aralash", "geom_tuzatildi", "kesildi"):
        allrows[c] = pd.to_numeric(allrows[c]).fillna(0).astype("int8")
    return allrows, tash.to_crs(g3857.crs), rep


def main(src, dst, args):
    if os.path.exists(dst):
        raise SystemExit(f"Chiqish fayli bor, ustiga yozmayman: {dst}")
    ichki = "--ichki-tekshiruv" in args
    ishchi = min(max(1, (os.cpu_count() or 2) - 2), 12)
    if "--ishchi" in args:
        ishchi = int(args[args.index("--ishchi") + 1])
    names = [a for i, a in enumerate(args) if not a.startswith("--") and not (i > 0 and args[i - 1] == "--ishchi")]
    t = pyogrio.read_dataframe(src, layer="ekin_yerlar", columns=["viloyat", "tuman"], read_geometry=False)
    size = t.groupby(["viloyat", "tuman"]).size()
    pairs = sorted(size.index) if "--hammasi" in args else sorted(p for p in size.index if p[1] in names)
    if not pairs:
        raise SystemExit("Tuman topilmadi")
    written = set()
    def write(df, layer):
        pyogrio.write_dataframe(df, dst, layer=layer, driver="GPKG", promote_to_multi=True, append=layer in written)
        written.add(layer)
    t_start = time.time()
    print(f"{len(pairs)} tuman, {ishchi} parallel jarayon", flush=True)
    with ProcessPoolExecutor(max_workers=ishchi) as ex:
        # kattalari birinchi yuboriladi (yuk tekis taqsimlanadi); yozish esa tuman nomi tartibida
        futs = {ex.submit(process, src, v, tm, ichki): (v, tm) for v, tm in sorted(pairs, key=lambda p: -size[p])}
        ready, nxt = {}, 0
        for f in as_completed(futs):
            ready[futs[f]] = f.result()            # ishchida xato bo'lsa shu yerda to'xtaydi
            while nxt < len(pairs) and pairs[nxt] in ready:
                rows, tash, rep = ready.pop(pairs[nxt]); nxt += 1
                write(rows, "ekin_yerlar")
                q = rows[rows.qoshilgan == 1]
                if len(q):
                    write(q, "qoshilgan")
                if len(tash):
                    write(tash, "tashlangan")
                print(f"[{nxt}/{len(pairs)}] " + " | ".join(f"{kk}={vv}" for kk, vv in rep.items()), flush=True)
    print(f"Tayyor: {time.time() - t_start:.0f} s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
