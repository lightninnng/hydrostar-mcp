"""Physical presentation data; full calculation records remain in their packages."""

import html
import json
from pathlib import Path

from hydrostar_mcp import __version__
from hydrostar_mcp.visualization import whole_mesh

ROOT = Path(__file__).resolve().parent.parent
NAMES = dict(
    vessel="曲线船体", container="集装箱船", tanker="丰满油船", platform="半潜平台"
)
FEATURES = {
    "vessel": "沿原创型值表曲线放样，水线和龙骨之间形成连续的四边形网格带。艏艉采用渐变站位，并保留少量端部过渡面元。",
    "container": "构型包含平行中体、圆舭、球鼻艏和艉封板，主尺度参考公开的 KCS 资料。节点和面元由本项目参数化建立。",
    "tanker": "构型包含丰满中体、宽平底和连续收缩的艏艉，尺度参数参考公开的 KVLCC2 资料，并保存了具体的曲面重建假设。",
    "platform": "构型包含中心柱、三个偏置扩底柱、连接杆件和压载，尺度参数参考公开的 OC4 资料。势流湿表面与 Morison 构件分别建模。",
}
NOTES = {
    "vessel": "质量、重心、惯性和恢复设置沿用曲线船体参照例的课程分析假设，附加横摇阻尼为 5%。本例在默认面元预算内采用较细的频率采样，适用于课程研究与所列条件下的一阶简化分析。",
    "container": "采用单刚体、零航速与自由漂浮条件。质量、重心、惯性、压载和阻尼按公开配置给出，主尺度参照与重建几何一并保存。",
    "tanker": "采用单刚体、零航速与自由漂浮条件。丰满船型、装载与阻尼均按本例明确假设设置，完整数值记录随公开输入保存。",
    "platform": "采用单刚体一阶势流与所列细杆模型。压载、组合重心、惯性和阻尼按配置给出，干结构提供几何背景，各计算分工随参数保存。",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def presentation_data():
    old = {c["key"]: c for c in read(ROOT / "docs/data/showcase.json")["cases"]}
    keys = [
        ("vessel", None),
        ("container", "container_kcs_style"),
        ("tanker", "tanker_kvlcc2_style"),
        ("platform", "semisub_oc4_style"),
    ]
    result = []
    for key, original in keys:
        if original is None:
            folder = ROOT / "examples/vessel"
            summary = read(folder / "verification.json")
            config = read(folder / "config.json")
            vertices, faces = whole_mesh(folder / "inputs/vessel.hst")
            vertices = [[round(v, 6) for v in p] for p in vertices]
            mesh, responses = summary["hslec"], read(folder / "motions.json")
            package, links = "examples/vessel", []
        else:
            item = old[original]
            summary, config = item["summary"], item["config"]
            vertices, faces = item["vertices"], item["faces"]
            mesh, responses = summary["mesh"], item["responses"]
            package = "examples/results/" + original
            links = [
                dict(title=s["title"], url=s["url"])
                for s in summary["reference_model"]["sources"].values()
            ]
        if set(summary["quality_gates"].values()) != {"passed"}:
            raise ValueError("Native execution gates failed: " + key)
        fields = ROOT / "examples/visualization/fields" / key
        condition, verification = (
            read(fields / "condition.json"),
            read(fields / "verification.json"),
        )
        if (
            set(verification["gates"].values()) != {"passed"}
            or verification["gates"].get("native_complex_wave") != "passed"
        ):
            raise ValueError("Native field checks failed: " + key)
        mechanics = summary["mechanics"]
        # The display canvas only needs geometry and slender-member settings.
        geometry = {
            k: v
            for k, v in config["geometry"].items()
            if k not in ("path", "source_manifest")
        }
        result.append(
            dict(
                key=key,
                label=NAMES[key],
                features=FEATURES[key],
                assumptions=NOTES[key],
                vertices=vertices,
                faces=faces,
                config=dict(
                    geometry=geometry,
                    mechanics=dict(morison=config["mechanics"]["morison"]),
                ),
                mechanics={
                    k: mechanics[k]
                    for k in ("mass_kg", "cog_m", "total_cb_m", "total_displacement_m3")
                },
                wet_panels=mesh["hull_panels"] * 2 ** mesh["symmetry"],
                total_panels=(mesh["hull_panels"] + mesh["waterplane_panels"])
                * 2 ** mesh["symmetry"],
                gm_roll_m=summary["solver_mechanics"]["gm_roll_pitch_m"][0],
                depth_m=config["environment"]["depth"],
                frequency_count=len(responses["heave"]["omega"]),
                headings=responses["heave"]["headings"],
                frequency_step=config["environment"]["frequency"]["step"],
                gates=summary["quality_gates"],
                package=package,
                source_links=links,
                animation={
                    k: condition[k]
                    for k in (
                        "omega_rad_s",
                        "period_s",
                        "heading_deg",
                        "wave_amplitude_m",
                        "depth_m",
                        "motion_gain",
                        "wave_height_gain",
                        "frames",
                        "playback_fps",
                        "body_panel_count",
                    )
                },
            )
        )
    return dict(version=__version__, cases=result)


def geometry_section():
    rows = []
    for c in read(ROOT / "docs/data/geometry.json")["cases"]:
        q = c["panel_quality"]
        key, label = c["key"], html.escape(c["label"])
        rows.append(
            f'<tr><td><a href="https://github.com/lightninnng/hydrostar-mcp/tree/main/examples/geometry/{key}">{label}</a></td><td>{q["quadrilaterals"]:,} / {q["triangles"]}</td><td>{c["full_equivalent_total"]:,}</td><td>{100 * c["volume_relative_error"]:.3f}%</td></tr>'
        )
    return (
        """<section aria-labelledby="geometry-heading"><h2 id="geometry-heading">5. 其他构型与建模方法</h2>
<p>同轴柱体采用轴向环带与周向对应，船体采用站位与剖面网格带，多边形及贯通开口采用相容分块。四边形保留到实际求解文件，并同时检查形状、翘曲、尺度过渡、水线闭环、拓扑、自交以及 CAD 体积与浮心。</p>
<p>下表保留已完成计算的几何研究参照。曲线船体和 Spar 的密网格沿用既定配置；前面的曲线船体展示采用新的 2873 个总面元方案。常规新模型按包含湿面、水线面和对称展开的 3000 个总面元预算规划，提高预算须按具体算例明确授权。</p>
<div class="table-wrap"><table><thead><tr><th>研究参照构型</th><th>湿面四边形 / 三角形</th><th>全体总面元</th><th>CAD 体积差</th></tr></thead><tbody>"""
        + "".join(rows)
        + """</tbody></table></div>
<p>型值表、曲线、DXF、CAD 和表面网格可沿统一流程进入湿表面建模。图像与 PDF 先完成尺寸标定和描线，再以独立尺寸点核对。资料接口及适用条件见<a href="https://github.com/lightninnng/hydrostar-mcp/blob/main/docs/geometry-sources.md">多来源建模说明</a>，结构分区与验收要求见<a href="https://github.com/lightninnng/hydrostar-mcp/blob/main/docs/panel-meshing.md">面元建模方法</a>。</p></section>"""
    )
