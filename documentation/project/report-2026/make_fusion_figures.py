"""Composite figures from the images embedded in the three Fusion 360 study reports
(mechanical/simulation/study-*.html): von Mises stress, total displacement (deformation),
safety factor, and the load / constraint set-up."""
import base64, re
from pathlib import Path
import io
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "analysis" / "flight-2026-09-30"))
import launch_figures as lf  # style + fonts

HERE = Path(__file__).resolve().parent
SIM = HERE.parents[2] / "mechanical" / "simulation"
STUDIES = [("study-1-horizontal-force", "Study 1 · Horizontal force, 30 N on +Z", "2.885 MPa", None),
           ("study-2-tearing-force", "Study 2 · Tearing force, 30 N on −X", "1.330 MPa", "0.026 mm"),
           ("study-3-impact-force", "Study 3 · Impact force, 100 N on −X", "2.345 MPa", "0.209 mm")]

def images(name):
    s = open(SIM / f"{name}.html", errors="ignore").read()
    out = []
    for m in re.finditer(r'<img[^>]*src="data:image/png;base64,([^"]{100,})"', s):
        d = base64.b64decode(m.group(1))
        if len(d) > 5000:
            out.append(Image.open(io.BytesIO(d)).convert("RGB"))
    return out   # 0 logo/model, 1 fixed, 2 force, 3 SF, 4 SF, 5 VM, 6 P1, 7 P3, 8 disp

for k, (name, title, vm, disp) in enumerate(STUDIES, 1):
    im = images(name)
    fixed, force, sf, vmi, dsp = im[1], im[2], im[3], im[5], im[8]
    def crop(i):
        w, h = i.size
        return i.crop((int(w * 0.30), 0, w, h))
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 4.55))
    fig.subplots_adjust(left=0.0, right=1.0, top=0.91, bottom=0.0, hspace=0.16, wspace=0.03)
    panels = [(crop(vmi), f"Von Mises stress · peak {vm}"), (crop(dsp), "Deformation (magnified)" + (f" · peak {disp}" if disp else "")),
              (crop(sf), "Safety factor · " + ("whole frame above the target (blue)" if k == 3 else "no region below the target (uncoloured)")), (None, "Constraint (blue face) and load (arrow)")]
    for ax, (img, t) in zip(axs.ravel(), panels):
        ax.axis("off"); ax.set_title(t, fontsize=7.8, loc="left", pad=3, color=lf.INK, fontweight="bold")
        if img is not None:
            ax.imshow(img)
        else:
            w = Image.new("RGB", (fixed.width * 2, fixed.height), "white")
            w.paste(fixed, (0, 0)); w.paste(force, (fixed.width, 0))
            ax.imshow(w)
    fig.suptitle(title, x=0.01, ha="left", fontsize=10, fontweight="bold", color=lf.INK, y=0.995)
    fig.savefig(HERE / "figures" / "photos" / f"fusion-study-{k}.jpg", dpi=200, bbox_inches="tight", pad_inches=0.08, pil_kwargs={"quality": 88})
    plt.close(fig)
    print("study", k)
