"""Mavjud v1 GPKG da Boshqa -> 'Mavsumiy ekin' (01_atribut_mavsum.py ga ham qo'shilgan).
python 01c_boshqa_mavsumiy.py <natija.gpkg>"""
import sys
from osgeo import ogr
ogr.UseExceptions()
ds = ogr.Open(sys.argv[1], 1)

def q(sql):
    r = ds.ExecuteSQL(sql)
    rows = [[f.GetField(i) for i in range(f.GetFieldCount())] for f in r] if r else []
    if r: ds.ReleaseResultSet(r)
    return rows

print("oldin (Boshqa, mavsum bo'sh):", q("SELECT COUNT(*) FROM ekin_yerlar WHERE turi='Boshqa' AND mavsum IS NULL"))
ds.ExecuteSQL("UPDATE ekin_yerlar SET mavsum='Mavsumiy ekin' WHERE turi='Boshqa'")
print("keyin:")
for row in q("SELECT turi, mavsum, COUNT(*) FROM ekin_yerlar WHERE mavsum IS NULL OR turi='Boshqa' GROUP BY turi, mavsum"):
    print("  ", row)
print("mavsum bo'yicha:")
for row in q("SELECT mavsum, COUNT(*), ROUND(SUM(maydon)) FROM ekin_yerlar GROUP BY mavsum"):
    print("  ", row)
ds = None
