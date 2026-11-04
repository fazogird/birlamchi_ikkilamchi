"""README rasmlari: jarayon sxemasi, mavsum konsepsiyasi, Excel namunasi (shaxsiy ma'lumotsiz varaqlardan).
python docs/rasmlar_yasash.py [xatolar_hisoboti.xlsx]"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Rectangle
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img")
os.makedirs(OUT, exist_ok=True)
C = {"blue": "#2F5597", "lb": "#DCE6F5", "green": "#3A7D44", "lg": "#E3F1E5", "or": "#C55A11", "lo": "#FBE5D6", "grey": "#595959"}


def box(ax, x, y, w, h, title, sub, fc, ec):
    # oddiy to'rtburchak (gis_pro muhitida FancyBboxPatch/bezier DLL xatosi beradi)
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=10.5, weight="bold", color=ec)
    ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center", fontsize=8.3, color=C["grey"], linespacing=1.3)


def arrow(ax, x1, y1, x2, y2):
    ax.add_patch(FancyArrow(x1, y1, x2 - x1, y2 - y1, width=0.02, head_width=0.14, head_length=0.14,
                            length_includes_head=True, color=C["grey"]))


def jarayon():
    fig, ax = plt.subplots(figsize=(13, 4.6), dpi=150)
    ax.set_xlim(0, 13); ax.set_ylim(0, 4.6); ax.axis("off")
    ax.text(0.1, 4.35, "1-BOSQICH:  1_TAYYORLASH.bat", fontsize=11, weight="bold", color=C["blue"])
    steps = [("Asl shp", "qishloq xo'jaligi\nekin konturlari"), ("01 Atribut", "apostrof, invalid,\nmavsum ustuni"),
             ("02 To'ldirish", "yetim mavsumlar,\nPaxta qoidasi, fermer"), ("03 Tekshiruv", "asl saqlanganmi,\nbalans, teshik"),
             ("04 Excel", "xatolar\nhisoboti")]
    for i, (t, s) in enumerate(steps):
        fc, ec = (C["lo"], C["or"]) if i == 0 else (C["lb"], C["blue"])
        box(ax, 0.1 + i * 2.55, 2.75, 2.15, 1.3, t, s, fc, ec)
        if i:
            arrow(ax, 0.1 + i * 2.55 - 0.4, 3.4, 0.1 + i * 2.55, 3.4)
    ax.text(0.1, 2.25, "Qo'lda: Excel bo'yicha ArcGIS da tuzatish (Save Edits)", fontsize=10, style="italic", color=C["grey"])
    arrow(ax, 11.0, 2.75, 7.4, 1.55)
    ax.text(0.1, 1.85, "2-BOSQICH:  2_EKSPORT.bat", fontsize=11, weight="bold", color=C["green"])
    box(ax, 5.2, 0.25, 3.3, 1.3, "05 Eksport", "multipart->singlepart, yangi uniqueid,\nsuv oylari, maydon", C["lg"], C["green"])
    box(ax, 9.6, 0.25, 3.3, 1.3, "Natija", "to'liq (backup) + qisqa (autsorsing)\nuchala faylda bir xil uniqueid", C["lg"], C["green"])
    box(ax, 0.6, 0.25, 3.3, 1.3, "3_QISQA_QAYTA.bat", "to'liqdan qisqa versiya\n(ID o'zgarmaydi)", "#F2F2F2", C["grey"])
    arrow(ax, 8.5, 0.9, 9.6, 0.9)
    fig.savefig(os.path.join(OUT, "jarayon.png"), bbox_inches="tight", facecolor="white"); plt.close(fig)


def konsepsiya():
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), dpi=150)
    col = {"Bug'doy": "#E6B655", "Mosh": "#7FB77E", "aniq": "#BFBFBF", "Kartoshka": "#A57FC2", "Paxta": "#F4F4F4"}
    def draw(ax, title, rows):
        ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off"); ax.set_title(title, fontsize=11, weight="bold")
        for y, lbl, parts in rows:
            ax.text(0, y + 0.45, lbl, fontsize=9.5, ha="left", va="center", weight="bold", color=C["grey"])
            x = 2.2
            for w, name, hatch, txt in parts:
                ax.add_patch(Rectangle((x, y), w, 0.9, fc=col.get(name, "white") if name else "white", ec="#404040",
                                       lw=1.2, hatch=hatch, ls="-" if name else "--"))
                ax.text(x + w / 2, y + 0.45, txt, ha="center", va="center", fontsize=8.5)
                x += w
        ax.add_patch(Rectangle((2.2, 0.35), 7.6, 0.35, fc="none", ec=C["blue"], lw=2))
        ax.text(6.0, 0.15, "to'liq dala: 4 ga", ha="center", va="top", fontsize=9, color=C["blue"])
    draw(axs[0], "Oldin: mavsum qatlamlarida teshik", [
        (3.3, "Birlamchi", [(3.8, "Bug'doy", None, "Bug'doy 2 ga"), (3.8, None, None, "chizilmagan")]),
        (1.6, "Ikkilamchi", [(3.8, "Mosh", None, "Mosh 2 ga"), (3.8, "Kartoshka", None, "Kartoshka 2 ga")])])
    draw(axs[1], "Keyin: har mavsumda dala to'liq yopilgan", [
        (3.3, "Birlamchi", [(3.8, "Bug'doy", None, "Bug'doy 2 ga"), (3.8, "aniq", "//", "Birlamchi ekin\naniqlanmagan (yangi)")]),
        (1.6, "Ikkilamchi", [(3.8, "Mosh", None, "Mosh 2 ga"), (3.8, "Kartoshka", None, "Kartoshka 2 ga")])])
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "konsepsiya.png"), bbox_inches="tight", facecolor="white"); plt.close(fig)


def excel(xlsx):
    """Faqat shaxsiy ma'lumotsiz varaqlar: Izoh (tavsif + soni) va Tuman_balans (yig'ma raqamlar)."""
    iz = pd.read_excel(xlsx, sheet_name="Izoh")
    iz["nima"] = iz["nima"].str.slice(0, 95) + "..."
    tb = pd.read_excel(xlsx, sheet_name="Tuman_balans")
    tb = tb[["viloyat", "tuman", "B_ga", "I_ga", "B_M_ostida", "farq_ga", "haqiqiy_teshik_m2"]].head(6)
    fig, axs = plt.subplots(2, 1, figsize=(13, 6.6), dpi=150, gridspec_kw={"height_ratios": [1.6, 1]})
    for ax, df, title, widths in ((axs[0], iz, "xatolar_hisoboti.xlsx — 'Izoh' varag'i (varaqlar ro'yxati)", [0.2, 0.68, 0.12]),
                                  (axs[1], tb, "'Tuman_balans' varag'i (namuna, birinchi 6 tuman)", None)):
        ax.axis("off"); ax.set_title(title, fontsize=11, weight="bold", loc="left")
        t = ax.table(cellText=df.astype(str).values, colLabels=df.columns, loc="upper center", cellLoc="left",
                     colLoc="left", colWidths=widths)
        t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1, 1.35)
        for (r, c), cell in t.get_celld().items():
            cell.set_edgecolor("#BFBFBF")
            if r == 0:
                cell.set_facecolor(C["blue"]); cell.set_text_props(color="white", weight="bold")
            elif r % 2 == 0:
                cell.set_facecolor("#F2F2F2")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "excel_namuna.png"), bbox_inches="tight", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    jarayon(); konsepsiya()
    if len(sys.argv) > 1:
        excel(sys.argv[1])
    print("Rasmlar:", sorted(os.listdir(OUT)))
