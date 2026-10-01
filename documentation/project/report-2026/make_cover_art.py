"""Cover artwork: the two measured descents drawn as light trails over a night sky."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
HERE = Path(__file__).resolve().parent
d = pd.read_csv(HERE.parents[2] / "analysis/flight-2026-09-30/flight_data_clean.csv")
rng = np.random.default_rng(7)
W, H = 8.27, 11.69
fig = plt.figure(figsize=(W, H), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
grad = np.linspace(0, 1, 512)[:, None]
cm = LinearSegmentedColormap.from_list("sky", ["#1d4ed8", "#0b2545", "#060f22"])
ax.imshow(grad[::-1], extent=[0, 1, 0, 1], cmap=cm, aspect="auto", alpha=1, zorder=0)
n = 520
x, y = rng.random(n), rng.random(n) ** 0.7
ax.scatter(x, y, s=rng.random(n) ** 3 * 9 + 0.3, color="white", alpha=0.65, lw=0, zorder=1)
# faint grid of altitude lines
for yy in np.linspace(0.08, 0.5, 8):
    ax.plot([0, 1], [yy, yy], color="white", alpha=0.04, lw=0.6, zorder=1)
def trail(g, xs, ys, color):
    from scipy.interpolate import PchipInterpolator
    t = np.linspace(0, 1, 400)
    xi = np.interp(t, np.linspace(0, 1, len(xs)), xs)
    yy = PchipInterpolator(np.linspace(0, 1, len(ys)), ys)(t)
    for lw, a in ((14, 0.05), (9, 0.09), (5, 0.18), (2.2, 0.9)):
        ax.plot(xi, yy, color=color, lw=lw, alpha=a, solid_capstyle="round", zorder=3)
    ax.scatter([xi[-1]], [yy[-1]], s=70, color="white", zorder=4)
f1 = d[(d.name == "F1") & (d.ti >= 677.3)]
f2 = d[d.name == "F2"]
h1 = f1.h_base.to_numpy(); h2 = f2.h_base.to_numpy() - f2.h_base.min()
trail(f1, np.linspace(0.40, 0.80, len(h1)), 0.06 + (h1 - h1.min()) / 30 * 0.17, "#60a5fa")
trail(f2, np.linspace(0.08, 0.50, len(h2)), 0.06 + h2 / 30 * 0.17, "#fb923c")
fig.savefig(HERE / "figures/cover_art.png", dpi=150)
