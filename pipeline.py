"""
Ekin yerlari: mavsum va to'liq dala — boshidan oxirigacha bitta dastur.

  1-BOSQICH  tayyorla : asl shp  ->  ekin_yerlar_yakuniy.gpkg + xatolar_hisoboti.xlsx (+ tekshiruv)
             (01 atribut/mavsum -> 02 to'ldirish -> 03 tekshiruv -> 04 Excel)
  ... foydalanuvchi Excel bo'yicha ArcGIS da qo'lda tuzatadi ...
  2-BOSQICH  eksport  : tuzatilgan gpkg  ->  ekin_yerlar_toliq.gpkg + ekin_yerlar_qisqa.gpkg   (05)
  QO'SHIMCHA qisqa    : to'liq versiya  ->  yangi qisqa versiya, uniqueid o'zgarmaydi          (06)

Ishga tushirish:
  1_TAYYORLASH.bat / 2_EKSPORT.bat  ni ikki marta bosing (fayl tanlash oynasi chiqadi), yoki:
  python pipeline.py tayyorla --shp <asl.shp> [--papka <chiqish papkasi>]
  python pipeline.py eksport  --kirish <yakuniy.gpkg> [--papka <chiqish papkasi>] [--format hex|arcgis]
Batafsil: QOLLANMA.md
"""
import os, sys, time, subprocess, argparse, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ROOT, "scripts")
KERAKLI_USTUNLAR = ["viloyat", "tuman", "region", "district", "maydon", "turi", "yil", "f_name", "f_inn", "f_cad",
                    "crop_id", "vh", "yld", "ekin_davri", "st_area_sh", "st_perimet", "shape_leng", "Shape_Le_1", "Shape_Area"]


def env_sozlash():
    """gis_pro muhitining GDAL/PROJ ma'lumot papkalarini o'rnatadi (conda activate qilinmagan bo'lsa ham ishlaydi)."""
    lib = os.path.join(sys.prefix, "Library", "share")
    for var, sub in (("GDAL_DATA", "gdal"), ("PROJ_LIB", "proj"), ("PROJ_DATA", "proj")):
        p = os.path.join(lib, sub)
        if os.path.isdir(p):
            os.environ[var] = p
    os.environ["PYTHONIOENCODING"] = "utf-8"


def tanlash(sarlavha, papka=False, turlar=None):
    """Fayl/papka tanlash oynasi; ishlamasa — matn so'rovi."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        r = tk.Tk(); r.withdraw(); r.attributes("-topmost", True)
        p = filedialog.askdirectory(title=sarlavha) if papka else filedialog.askopenfilename(title=sarlavha, filetypes=turlar)
        r.destroy()
        if p:
            return os.path.normpath(p)
    except Exception:
        pass
    p = input(f"{sarlavha}: ").strip().strip('"')
    return os.path.normpath(p) if p else ""


class Jurnal:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8")
    def __call__(self, msg=""):
        print(msg, flush=True)
        self.f.write(msg + "\n"); self.f.flush()


def qadam(log, nom, skript, args):
    log(f"\n{'=' * 70}\n{nom}\n{'=' * 70}")
    t0 = time.time()
    cmd = [sys.executable, "-I", os.path.join(SCRIPTS, skript)] + args
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    for line in p.stdout:
        line = line.rstrip()
        if any(s in line for s in ("GDAL_DATA", "header.dxf", "_init_gdal")):
            continue
        log(line)
    p.wait()
    if p.returncode != 0:
        log(f"\n!!! XATO: '{nom}' bosqichi to'xtadi (kod {p.returncode}). Yuqoridagi xabarni o'qing.")
        raise SystemExit(1)
    log(f"--- {nom}: tayyor ({time.time() - t0:.0f} s)")


def shp_tekshir(shp, log):
    import pyogrio
    info = pyogrio.read_info(shp, encoding="utf-8")
    miss = [c for c in KERAKLI_USTUNLAR if c not in info["fields"]]
    log(f"Kirish fayli: {shp}\n  poligonlar: {info['features']}, CRS: {info['crs']}, geometriya: {info['geometry_type']}")
    if miss:
        log(f"!!! XATO: shp da quyidagi ustunlar yo'q: {miss}")
        raise SystemExit(1)
    a = pyogrio.read_dataframe(shp, columns=["viloyat", "tuman", "turi"], read_geometry=False, encoding="utf-8")
    nul = int(a.viloyat.isna().sum() + a.tuman.isna().sum())
    log(f"  viloyatlar: {a.viloyat.nunique()}, tumanlar: {a.groupby(['viloyat', 'tuman']).ngroups}, ekin turlari: {a.turi.nunique()}")
    if nul:
        log(f"!!! XATO: {nul} ta qatorda viloyat yoki tuman bo'sh — avval shp da to'ldiring.")
        raise SystemExit(1)


def tayyorla(a):
    shp = a.shp or tanlash("Asl ekin yerlari shp faylini tanlang", turlar=[("Shapefile", "*.shp"), ("GeoPackage", "*.gpkg")])
    if not shp or not os.path.exists(shp):
        raise SystemExit(f"Fayl topilmadi: {shp}")
    nom = os.path.splitext(os.path.basename(shp))[0]
    papka = a.papka or os.path.join(ROOT, f"natija_{nom}_{datetime.datetime.now():%Y%m%d_%H%M%S}")
    os.makedirs(papka, exist_ok=True)
    v1, yak = os.path.join(papka, "ekin_yerlar_v1.gpkg"), os.path.join(papka, "ekin_yerlar_yakuniy.gpkg")
    xls, bal = os.path.join(papka, "xatolar_hisoboti.xlsx"), os.path.join(papka, "ekin_yerlar_yakuniy_tuman_balans.csv")
    band = [f for f in (v1, yak, xls) if os.path.exists(f)]
    if band:
        raise SystemExit(f"Papkada natija fayllari allaqachon bor, ustiga yozilmaydi: {band}\nBoshqa (bo'sh) papka tanlang.")
    log = Jurnal(os.path.join(papka, "jurnal.txt"))
    t0 = time.time()
    log(f"1-BOSQICH: TAYYORLASH — {datetime.datetime.now():%Y-%m-%d %H:%M}\nNatija papkasi: {papka}")
    shp_tekshir(shp, log)
    qadam(log, "1/4  Atributlar va mavsum (apostrof, buzuq geometriya, mavsum ustuni)", "01_atribut_mavsum.py", [shp, v1])
    qadam(log, "2/4  Mavsumlarni to'ldirish, Paxta qoidasi, fermer ma'lumoti, maydon (tumanlar parallel)",
          "02_dala_toldirish.py", [v1, yak, "--hammasi"] + (["--ishchi", str(a.ishchi)] if a.ishchi else []))
    qadam(log, "3/4  Yakuniy tekshiruv (balans, teshik, asl ma'lumot saqlanganmi)", "03_yakuniy_tekshirish.py",
          [v1, yak] + (["--ishchi", str(a.ishchi)] if a.ishchi else []))
    qadam(log, "4/4  Xatolar hisoboti (Excel)", "04_xatolar_excel.py", [v1, yak, xls, bal])
    log(f"\n1-BOSQICH TUGADI ({(time.time() - t0) / 60:.1f} daqiqa).\n"
        f"  Yakuniy fayl:    {yak}\n  Xatolar (Excel): {xls}\n  Jurnal:          {os.path.join(papka, 'jurnal.txt')}\n"
        f"KEYINGI QADAM: Excel ni ko'rib, ArcGIS da {os.path.basename(yak)} ni kerak bo'lsa qo'lda tuzating,\n"
        f"so'ng 2_EKSPORT.bat ni ishga tushirib shu faylni tanlang.")


def eksport(a):
    kir = a.kirish or tanlash("Tuzatilgan ekin_yerlar_yakuniy.gpkg faylini tanlang", turlar=[("GeoPackage", "*.gpkg")])
    if not kir or not os.path.exists(kir):
        raise SystemExit(f"Fayl topilmadi: {kir}")
    papka = a.papka or os.path.dirname(kir)
    os.makedirs(papka, exist_ok=True)
    vaqt = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
    tol, qis = os.path.join(papka, f"ekin_yerlar_toliq_{vaqt}.gpkg"), os.path.join(papka, f"ekin_yerlar_qisqa_{vaqt}.gpkg")
    log = Jurnal(os.path.join(papka, "jurnal.txt"))
    log(f"\n2-BOSQICH: EKSPORT — {datetime.datetime.now():%Y-%m-%d %H:%M}\nKirish: {kir}")
    qadam(log, "Multipart->Singlepart, yangi uniqueid, suv oylari, to'liq va qisqa versiya", "05_uniqueid_eksport.py",
          [kir, tol, qis, "--format", a.format])
    log(f"\n2-BOSQICH TUGADI.\n  To'liq (backup): {tol}\n  Qisqa:           {qis}")


def qisqa(a):
    kir = a.kirish or tanlash("To'liq versiyani (ekin_yerlar_toliq_*.gpkg) tanlang", turlar=[("GeoPackage", "*.gpkg")])
    if not kir or not os.path.exists(kir):
        raise SystemExit(f"Fayl topilmadi: {kir}")
    papka = a.papka or os.path.dirname(kir)
    os.makedirs(papka, exist_ok=True)
    qis = os.path.join(papka, f"ekin_yerlar_qisqa_{datetime.datetime.now():%Y%m%d_%H%M%S}.gpkg")
    log = Jurnal(os.path.join(papka, "jurnal.txt"))
    log(f"\nQISQA VERSIYANI QAYTA YASASH — {datetime.datetime.now():%Y-%m-%d %H:%M}\nKirish (to'liq): {kir}")
    qadam(log, "To'liqdan qisqa versiya (uniqueid o'zgarmaydi, Baliqxovuz/Issiqxona chiqariladi)", "06_qisqa_versiya.py", [kir, qis])
    log(f"\nTAYYOR. Qisqa: {qis}")


def main():
    env_sozlash()
    ap = argparse.ArgumentParser(description="Ekin yerlari: mavsum va to'liq dala (QOLLANMA.md)")
    sub = ap.add_subparsers(dest="bosqich", required=True)
    t = sub.add_parser("tayyorla", help="1-bosqich: asl shp -> yakuniy gpkg + Excel")
    t.add_argument("--shp"); t.add_argument("--papka"); t.add_argument("--ishchi", type=int)
    e = sub.add_parser("eksport", help="2-bosqich: tuzatilgan gpkg -> to'liq va qisqa versiya")
    e.add_argument("--kirish"); e.add_argument("--papka"); e.add_argument("--format", default="hex", choices=["hex", "arcgis"])
    k = sub.add_parser("qisqa", help="to'liq versiyadan qisqa versiyani qayta yasash (uniqueid o'zgarmaydi)")
    k.add_argument("--kirish"); k.add_argument("--papka")
    a = ap.parse_args()
    {"tayyorla": tayyorla, "eksport": eksport, "qisqa": qisqa}[a.bosqich](a)


if __name__ == "__main__":
    main()
