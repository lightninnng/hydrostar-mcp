"""Build an offline results page with embedded numerical data and local media."""

import json
import html
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from hydrostar_mcp import __version__


def geometry_section():
    data = json.loads((ROOT / "docs/data/geometry.json").read_text(encoding="utf-8"))
    parts = [
        '<section aria-labelledby="geometry-heading"><h2 id="geometry-heading">5. 多来源复杂几何与原生计算</h2>',
        "<p>以下三个原创算例使用统一几何前处理，分别验证曲线型值表、带贯通开口的多边形放样和毫米制 STEP 组合实体。湿面经过单位、坐标、水线、法向、拓扑、自交以及 CAD 体积与浮心核对，再由 HydroStar 完成单刚体一阶频域计算。</p>",
        '<figure><img class="motion-image" src="assets/geometry-source-cases.png" loading="lazy" alt="三个原创复杂几何的实际求解湿表面"><figcaption>图 4. 曲线站位船体、带月池的多边形浮体及带有限厚升沉板的 Spar。坐标采用米，体积与 CAD 偏差按各自实际网格积分给出。完整参数和来源文件随算例保存。</figcaption></figure>',
    ]
    for c in data["cases"]:
        key, label = c["key"], html.escape(c["label"])
        parts.append(
            f"<h3>{label}</h3><p>本算例采用 {c['panels']:,} 个全体湿面元及 {c['waterplane_panels']:,} 个水线面元。湿面排水体积为 {c['volume_m3']:,.3f} m³，与 CAD 实体的相对差为 {100 * c['volume_relative_error']:.3f}%，浮心距离偏差为 {c['cb_distance_m']:.4f} m。六项原生执行质量门禁均通过。</p>"
        )
        parts.append(
            f'<details><summary>查看{label}的几何验收与六自由度响应图</summary><figure><img class="motion-image" src="{c["geometry_figure"]}" loading="lazy" alt="{label}的几何验收"><figcaption>平均水线以下的完整湿表面及投影。剖面资料使用橙色显示。</figcaption></figure><figure><img class="motion-image" src="{c["rao_figure"]}" loading="lazy" alt="{label}的原生六自由度响应"><figcaption>0.2–0.8 rad/s、步长 0.1 rad/s，浪向为 0°、60°、120° 和 180°。折线连接原生频率点。</figcaption></figure></details>'
        )
        parts.append(
            f'<p class="data-links"><a href="https://github.com/lightninnng/hydrostar-mcp/tree/main/examples/geometry/{key}">源资料、参数、原生输入、完整数组与验收记录</a>随公开仓库保存。</p>'
        )
    parts.append(
        '<p>这组频率用于核验几何到计算的链路。装载采用网格排水配平、浮心以下 1 m 的重心、包络尺度估算的回转半径和 5% 附加横摇阻尼，均为显式示例假设。具体工程用途应补充实际质量惯性、约束与阻尼、峰区和空间敏感性以及参考响应。</p><p>型值表、DXF、CAD、表面网格与标定图纸的输入方法见<a href="https://github.com/lightninnng/hydrostar-mcp/blob/main/docs/geometry-sources.md">多来源几何建模与验收</a>。当前物理编排采用单刚体，结构柔性、多体运动和实际系泊预载按目标问题扩展。</p></section>'
    )
    return "\n".join(parts)


def main():
    data = json.loads((ROOT / "docs/data/showcase.json").read_text(encoding="utf-8"))
    if len(data["cases"]) != 3:
        raise ValueError("The gallery requires three verified cases")
    for model in data["cases"]:
        folder = ROOT / "examples/animations" / model["key"]
        field = json.loads((folder / "field.json").read_text(encoding="utf-8"))
        render = json.loads((folder / "render.json").read_text(encoding="utf-8"))
        verification = json.loads(
            (folder / "verification.json").read_text(encoding="utf-8")
        )
        model["animation"] = dict(
            omega_rad_s=field["omega_rad_s"],
            heading_deg=field["heading_deg"],
            wave_amplitude_m=field["wave_amplitude_m"],
            depth_m=field["depth_m"],
            period_s=render["period_s"],
            motion_gain=render["motion_gain"],
            frames=render["frames"],
            source_case_id=verification["source_case_id"],
            field_points=verification["point_count"],
            wave_reference_xy_m=field["wave_reference_xy_m"],
        )
    for model in data["cases"]:
        folder = ROOT / "examples/pressures" / model["key"]
        verification = json.loads(
            (folder / "verification.json").read_text(encoding="utf-8")
        )
        render = json.loads((folder / "render.json").read_text(encoding="utf-8"))
        if set(verification["pressure_gates"].values()) != {"passed"}:
            raise ValueError("Pressure validation must pass before building the report")
        model["pressure"] = {
            k: verification[k]
            for k in [
                "panel_count",
                "incident_complex_max_error",
                "hydrostatic_motion_complex_max_error",
                "offset_complex_change_over_global_peak",
                "pressure_colour_limit_kpa",
            ]
        }
        model["pressure"].update(
            motion_gain=render["motion_gain"],
            source_case_id=verification["source_case_id"],
        )
    (ROOT / "docs/data/showcase.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    payload = (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    template = (ROOT / "scripts/templates/gallery.html").read_text(encoding="utf-8")
    (ROOT / "docs/index.html").write_text(
        template.replace("__SHOWCASE_DATA__", payload)
        .replace("__VERSION__", __version__)
        .replace("__GEOMETRY_STUDY__", geometry_section()),
        encoding="utf-8",
    )
    print(ROOT / "docs/index.html")


if __name__ == "__main__":
    main()
