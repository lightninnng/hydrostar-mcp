"""Scientific figures from validated solver output (optional matplotlib extra)."""

from pathlib import Path
import math

from . import core

LABELS = {
    "container_kcs_style": "Container hull | KCS-informed",
    "tanker_kvlcc2_style": "Full-form tanker | KVLCC2-informed",
    "semisub_oc4_style": "Column semisubmersible | OC4-informed",
}
# Okabe-Ito palette; line styles preserve identification in grayscale.
COLORS = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]


def _scientific_style(plt):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "axes.linewidth": 0.8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "grid.linewidth": 0.6,
            "pdf.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def _save_figure(fig, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=300, facecolor="white")
    # Vector companion for reports, presentations and publication layout.
    if destination.suffix.lower() == ".png":
        fig.savefig(destination.with_suffix(".pdf"), facecolor="white")
    return destination


def whole_mesh(path):
    nodes, panels, meta = core.read_hst(path)
    ids = {k: i for i, k in enumerate(nodes)}
    vertices = [list(p) for p in nodes.values()]
    faces = [[ids[v] for v in dict.fromkeys(p)] for p in panels]
    sym = int(meta["SYMMETRY_BODY"][0][1])
    for axis in [1, 0] if sym == 2 else [1] if sym == 1 else []:
        count = len(vertices)
        vertices.extend(
            [[(-v if k == axis else v) for k, v in enumerate(p)] for p in vertices[:]]
        )
        faces.extend([[v + count for v in reversed(p)] for p in faces[:]])
    return vertices, faces


def dry_columns(config):
    g = config["geometry"]
    if g["type"] != "column_semisub":
        return []
    R = g["offset_radius"]
    return [
        (0.0, 0.0, g["center_diameter"] / 2, 10.0),
        (-R, 0.0, g["upper_diameter"] / 2, g["freeboard"]),
        (R / 2, math.sqrt(3) * R / 2, g["upper_diameter"] / 2, g["freeboard"]),
        (R / 2, -math.sqrt(3) * R / 2, g["upper_diameter"] / 2, g["freeboard"]),
    ]


def plot_rao(responses, destination, title="HydroStar | Six-DOF response"):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _scientific_style(plt)
    sample = responses["heave"]
    headings = [h for h in [0, 60, 90, 180] if h in sample["headings"]] or sample[
        "headings"
    ][:4]
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
    for index, (ax, dof) in enumerate(zip(axes.flat, core.DOFS)):
        a = responses[dof]
        for j, head in enumerate(headings):
            column = a["headings"].index(head)
            ax.plot(
                a["omega"],
                [row[column] for row in a["amplitude"]],
                label=f"{head:g}\N{DEGREE SIGN}",
                color=COLORS[j],
                ls=["-", "-.", "--", ":"][j],
                lw=1.6,
            )
        ax.set_title(f"({chr(97 + index)}) {dof.capitalize()}", loc="left")
        ax.set_ylabel(f"RAO amplitude ({a['unit']})")
        ax.set_ylim(bottom=0)
        ax.grid(alpha=0.2)
        ax.minorticks_on()
        ax.tick_params(which="minor", length=2)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel(r"Wave angular frequency, $\omega$ (rad s$^{-1}$)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    title = title.replace(" | Native six-DOF RAO", "")
    fig.suptitle(title, fontsize=15, y=0.976)
    fig.text(
        0.5,
        0.937,
        "Six-degree-of-freedom response amplitude operators",
        ha="center",
        color="#526278",
    )
    fig.legend(
        handles,
        labels,
        ncol=len(headings),
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        frameon=False,
    )
    fig.text(
        0.5,
        0.026,
        "HydroStar 8.2.0 | Native frequency samples joined by straight segments | Headings relative to model +x axis",
        ha="center",
        color="#526278",
        fontsize=9,
    )
    fig.subplots_adjust(
        left=0.08, right=0.98, bottom=0.10, top=0.84, hspace=0.39, wspace=0.24
    )
    destination = _save_figure(fig, destination)
    plt.close(fig)
    return destination


def plot_geometry(models, destination):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    _scientific_style(plt)
    fig = plt.figure(figsize=(16, 5.3))
    for index, m in enumerate(models):
        ax = fig.add_subplot(1, len(models), index + 1, projection="3d")
        vertices = m["vertices"]
        points = vertices[:]
        ax.add_collection3d(
            Poly3DCollection(
                [[vertices[i] for i in p] for p in m["faces"]],
                facecolor="#0072B2",
                edgecolor="#305c70",
                lw=0.13,
                alpha=0.86,
            )
        )
        for x, y, r, z in dry_columns(m["config"]):
            a = [
                (
                    x + r * math.cos(2 * math.pi * j / 24),
                    y + r * math.sin(2 * math.pi * j / 24),
                    0.0,
                )
                for j in range(25)
            ]
            b = [(xx, yy, z) for xx, yy, _ in a]
            points += b
            ax.add_collection3d(
                Poly3DCollection(
                    [[a[j], a[j + 1], b[j + 1], b[j]] for j in range(24)],
                    facecolor="#879aa6",
                    edgecolor="#879aa6",
                    lw=0.25,
                    alpha=0.18,
                )
            )
        for rod in m["config"]["mechanics"]["morison"]:
            if rod["cm"] <= 0:
                continue
            a, b = rod["start"], rod["end"]
            points += [a, b]
            ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]], color="#D55E00", lw=1.5)
        low = [min(p[k] for p in points) for k in range(3)]
        high = [max(p[k] for p in points) for k in range(3)]
        ax.set(
            xlim=(low[0] - 2, high[0] + 2),
            ylim=(low[1] - 2, high[1] + 2),
            zlim=(low[2] - 2, high[2] + 2),
        )
        ax.set_box_aspect([high[k] - low[k] + 4 for k in range(3)])
        for a in (ax.xaxis, ax.yaxis, ax.zaxis):
            a.set_major_locator(MaxNLocator(3))
        ax.set(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)")
        ax.view_init(23, -50 if index < 2 else -35)
        ax.set_title(
            f"({chr(97 + index)}) " + LABELS.get(m["key"], m["key"]),
            pad=12,
            fontsize=10,
        )
    fig.suptitle("Source-informed reference configurations", fontsize=16, y=0.97)
    fig.text(
        0.5,
        0.035,
        "Blue: solved wet panels | Vermilion: physical slender members | Gray: dry-column context | Equal axis scales within each view",
        ha="center",
        color="#526278",
        fontsize=9,
    )
    fig.subplots_adjust(left=0.01, right=0.99, top=0.85, bottom=0.12, wspace=0.03)
    destination = _save_figure(fig, destination)
    plt.close(fig)
    return destination


def plot_case(service, case_id, destination=None):
    report = service.status(case_id)
    responses = {d: service.result(case_id, d) for d in core.DOFS}
    target = (
        Path(destination)
        if destination
        else service.case_path(case_id) / "plots/rao.png"
    )
    plot_rao(responses, target, title=report["project"] + " | Six-DOF RAO")
    return dict(status="plotted", case_id=case_id, image_path=str(target.resolve()))
