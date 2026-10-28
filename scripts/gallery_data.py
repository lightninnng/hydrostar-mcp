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
                frequency_range_rad_s=[
                    responses["heave"]["omega"][0],
                    responses["heave"]["omega"][-1],
                ],
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


def result_sections(dataset):
    """Build visible result chapters from the same accepted media as README."""
    cases = {case["key"]: case for case in dataset["cases"]}
    previews = {
        item["preview"]: item
        for item in read(ROOT / "examples/visualization/readme-media.json")["media"]
    }
    sections = []
    for section, key in enumerate(("vessel", "platform", "container", "tanker"), 2):
        case = cases[key]
        label = html.escape(case["label"])
        first, last = case["frequency_range_rad_s"]
        animation = case["animation"]
        headings = "".join(
            f'<option value="{value:g}"'
            + (" selected" if value == 60 else "")
            + f">{value:g}°</option>"
            for value in case["headings"]
        )
        condition = (
            f"波幅为 {animation['wave_amplitude_m']:.2f} m，浪向为 "
            f"{animation['heading_deg']:g}°，角频率为 {animation['omega_rad_s']:g} rad/s，"
            f"物理周期为 {animation['period_s']:.3f} s，水深为 {animation['depth_m']:g} m。"
        )
        figures = []
        for suffix, title, letter, caption in (
            (
                "coupled",
                "表面压力、波面与运动",
                "b",
                "左图为平均湿表面的随体一阶动态压力，单位为 kPa；中图为总波面与刚体运动；"
                "右图为包含绕射与运动诱导辐射的散射波面。压力图几何倍率为 1。",
            ),
            (
                "components",
                "绕射与辐射波场",
                "c",
                "左图为固定平均姿态下的绕射波面，右图为六自由度运动共同产生的辐射波面。"
                "分量在复数域分解后，采用同一物理相位重建。",
            ),
        ):
            preview = f"docs/assets/readme-{key}-{suffix}.gif"
            if preview not in previews:
                raise ValueError("Accepted README preview required: " + preview)
            native = previews[preview]
            if native["source"] != f"docs/assets/{key}-{suffix}.gif":
                raise ValueError("Native preview source differs: " + preview)
            image_id = f"{key}-{suffix}"
            still = f"assets/{key}-{suffix}-frame.png"
            original_width = 2160 if suffix == "coupled" else 1440
            figures.append(
                f'''<figure class="native-animation" data-case="{key}" data-view="{suffix}">
<div class="figure-toolbar"><h3>{title}</h3><button type="button" class="animation-toggle" aria-controls="{image_id}" aria-pressed="false" aria-label="{label}{title}：播放动图">播放动图</button></div>
<div class="media-viewport"><img id="{image_id}" class="media-image" src="{still}" data-still="{still}" data-animation="{preview.removeprefix("docs/")}" width="{original_width}" height="810" loading="lazy" decoding="async" alt="{label}，{title}，原生计算场量"></div>
<figcaption>图 {section}{letter}。{caption}波面色标为 m，波高和运动均采用 6 倍观察倍率。每个面板使用完整周期内固定的色标。<a href="assets/{key}-{suffix}.gif" target="_blank" rel="noopener">查看高清动图</a>。</figcaption></figure>'''
            )
        sources = "".join(
            f'<p><a href="{html.escape(source["url"], quote=True)}" rel="noreferrer">{html.escape(source["title"])}</a></p>'
            for source in case["source_links"]
        )
        if not sources:
            sources = "<p>曲线船体使用本项目原创型值表，尺寸、坐标、单位、放样方法与装载假设随算例保存。</p>"
        sections.append(
            f'''<section class="case-report" id="case-{key}" data-result-case="{key}" aria-labelledby="{key}-heading">
<div class="case-heading"><h2 id="{key}-heading">{section}. {label}</h2><a href="#model-heading" data-inspect-model="{key}">查看交互网格</a></div>
<p>{html.escape(case["features"])}全体湿面共 {case["wet_panels"]:,} 个面元，包含水线面的总数为 {case["total_panels"]:,}。{html.escape(case["assumptions"])}</p>
<figure class="response-overview"><h3>六自由度频率响应</h3><a href="assets/{key}-response.pdf" target="_blank" rel="noopener"><img class="media-image" src="assets/{key}-response.png" width="2400" height="1540" loading="lazy" decoding="async" alt="{label}，五个浪向的六自由度响应幅值"></a>
<figcaption>图 {section}a。原生响应覆盖 {first:g}–{last:g} rad/s，步长为 {case["frequency_step"]:g} rad/s，共 {case["frequency_count"]} 个频率点和 {len(case["headings"])} 个浪向。图中叠加 0°、60°、90°、120° 和 180° 浪向；平移幅值为 m/m，转动幅值为 deg/m。点击图片查看矢量 PDF。</figcaption></figure>
<details class="response-detail" data-response-case="{key}"><summary>按浪向查看幅值与相位</summary>
<div class="toolbar"><label class="field">响应浪向<select class="response-heading" aria-label="{label}响应浪向">{headings}</select></label><div class="tabs" role="group" aria-label="{label}响应类型"><button type="button" data-mode="amplitude" aria-pressed="true">幅值</button><button type="button" data-mode="phase" aria-pressed="false">相位</button></div></div>
<figure><div class="media-viewport"><img class="media-image curve response-curve" src="assets/{key}-amplitude-60.svg" width="1400" height="900" loading="lazy" alt="{label}，60 度浪向，六自由度幅值"></div><figcaption class="response-caption">平移幅值单位为 m/m，转动幅值为 deg/m，横轴为波浪角频率（rad/s）。</figcaption></figure><p class="data-links"><a class="response-original" href="assets/{key}-amplitude-60.svg" target="_blank" rel="noopener">查看当前矢量原图</a>。窄屏可横向查看完整图幅。</p></details>
<p class="case-condition">本节动画采用同一规则波工况。{condition}</p>
{"".join(figures)}
<p class="source">每组动图完整保留 40 个物理相位，以 10 帧/秒循环播放，一次播放循环为 4 秒；真实物理时刻见 t 和 t/T。不同构型和面板采用各自标明的色标范围，颜色保持实际物理量。灰色干结构和细杆提供空间背景。</p>
<p class="data-links">本构型的<a href="https://github.com/lightninnng/hydrostar-mcp/tree/main/{case["package"]}">模型参数与原生计算文件</a>、<a href="https://github.com/lightninnng/hydrostar-mcp/tree/main/examples/visualization/fields/{key}">场量与导出设置</a>随仓库提供。<a href="assets/{key}-wave.gif" target="_blank" rel="noopener">总波与散射波的放大视图</a>可单独打开。</p>
<details><summary>{label}的资料来源</summary><div class="source sources">{sources}</div></details></section>'''
        )
    return "\n".join(sections)


def overview_table(dataset):
    """Summarize the four native sweeps beside the native mesh plate."""
    cases = {case["key"]: case for case in dataset["cases"]}
    rows = []
    for key in ("vessel", "platform", "container", "tanker"):
        case = cases[key]
        first, last = case["frequency_range_rad_s"]
        rows.append(
            f'<tr><th scope="row"><a href="#case-{key}">{html.escape(case["label"])}</a></th>'
            f"<td>{case['total_panels']:,}</td><td>{first:g}–{last:g}</td>"
            f"<td>{case['frequency_count']} × {len(case['headings'])}</td></tr>"
        )
    return "".join(rows)


def acceptance_table(dataset):
    cases = {case["key"]: case for case in dataset["cases"]}
    names = dict(
        semantic_input="输入语义与质量惯性",
        static_equilibrium="静力平衡",
        mesh_geometry="网格几何",
        mesh_topology="网格拓扑",
        module_execution="原生模块执行",
        rao_integrity="响应结果完整性",
    )
    rows = []
    for gate, label in names.items():
        cells = []
        for key in ("vessel", "platform", "container", "tanker"):
            if cases[key]["gates"].get(gate) != "passed":
                raise ValueError("Publication acceptance failed: " + key + ": " + gate)
            cells.append("<td>通过</td>")
        rows.append(f'<tr><th scope="row">{label}</th>{"".join(cells)}</tr>')
    return "".join(rows)


def geometry_section():
    rows = []
    for c in read(ROOT / "docs/data/geometry.json")["cases"]:
        q = c["panel_quality"]
        key, label = c["key"], html.escape(c["label"])
        rows.append(
            f'<tr><td><a href="https://github.com/lightninnng/hydrostar-mcp/tree/main/examples/geometry/{key}">{label}</a></td><td>{q["quadrilaterals"]:,} / {q["triangles"]}</td><td>{c["full_equivalent_total"]:,}</td><td>{100 * c["volume_relative_error"]:.3f}%</td></tr>'
        )
    return (
        """<section aria-labelledby="geometry-heading"><h2 id="geometry-heading">8. 其他构型与建模方法</h2>
<p>同轴柱体采用轴向环带与周向对应，船体采用站位与剖面网格带，多边形及贯通开口采用相容分块。四边形保留到实际求解文件，并同时检查形状、翘曲、尺度过渡、水线闭环、拓扑、自交以及 CAD 体积与浮心。</p>
<p>下表保留已完成计算的几何研究参照。曲线船体和 Spar 的密网格沿用既定配置；前面的曲线船体展示采用新的 2873 个总面元方案。常规新模型按包含湿面、水线面和对称展开的 3000 个总面元预算规划，提高预算须按具体算例明确授权。</p>
<div class="table-wrap"><table><thead><tr><th>研究参照构型</th><th>湿面四边形 / 三角形</th><th>全体总面元</th><th>CAD 体积差</th></tr></thead><tbody>"""
        + "".join(rows)
        + """</tbody></table></div>
<p>型值表、曲线、DXF、CAD 和表面网格可沿统一流程进入湿表面建模。图像与 PDF 先完成尺寸标定和描线，再以独立尺寸点核对。资料接口及适用条件见<a href="https://github.com/lightninnng/hydrostar-mcp/blob/main/docs/geometry-sources.md">多来源建模说明</a>，结构分区与验收要求见<a href="https://github.com/lightninnng/hydrostar-mcp/blob/main/docs/panel-meshing.md">面元建模方法</a>。</p></section>"""
    )


def second_order_section():
    """Present the computed platform load study with component-level scope."""
    record = read(ROOT / "examples/second-order/platform/verification.json")
    surface = read(ROOT / "examples/second-order/platform/geometry/surface.json")
    if record["status"] != "verified_with_component_limitations":
        raise ValueError("Second-order acceptance scope required")
    figures = []
    for kind, letter, title, caption in (
        (
            "drift",
            "b",
            "二阶平均漂移荷载",
            "近场六分量结果与可用的远场分量叠加比较。水平漂移力近远场差异最高为 3.76%；艏摇力矩的差异在下文单列。",
        ),
        (
            "qtf",
            "c",
            "完整差频 QTF 幅值",
            "展示差频为 0、0.05 和 0.10 rad/s 的六分量幅值。三条曲线采用共同有效区间 0.50–1.00 rad/s，完整数据保留全部有效配对。",
        ),
        (
            "complex",
            "d",
            "差频荷载的实部与虚部",
            "差频为 0.10 rad/s，实部与虚部共同保留原生复数荷载及其相位信息。",
        ),
        (
            "sensitivity",
            "e",
            "外部积分网格敏感性",
            "两档计算保持湿面、质量、重心、惯性、恢复、阻尼和外部域半径一致，改变近体自由面的积分离散。图示差频为 0.10 rad/s。",
        ),
    ):
        figures.append(
            f'<figure class="response-overview" data-second-order="{kind}"><h3>{title}</h3><a href="assets/platform-second-order-{kind}.pdf" target="_blank" rel="noopener"><img class="media-image" src="assets/platform-second-order-{kind}.png" width="2400" height="1540" loading="lazy" decoding="async" alt="半潜平台，{title}，原生二阶计算"></a><figcaption>图 6{letter}。{caption}力系数单位为 kN/m²，力矩系数为 kN m/m²。点击图片查看矢量 PDF，也可查看<a href="assets/platform-second-order-{kind}.svg" target="_blank" rel="noopener">原生 SVG</a>。</figcaption></figure>'
        )
    rows = []
    labels = dict(
        fx="纵向力",
        fy="横向力",
        fz="垂向力",
        mx="横摇力矩",
        my="纵摇力矩",
        mz="艏摇力矩",
    )
    for name, label in labels.items():
        error = 100 * record["surface_sensitivity"][name]["relative_to_own_peak"]
        accepted = record["component_acceptance"][name]
        state = (
            "通过本例 0.5% 敏感性门限"
            if accepted == "passed_example_sensitivity_gate"
            else "需继续收敛研究"
        )
        rows.append(
            f'<tr><th scope="row">{label}</th><td>{error:.3f}%</td><td>{state}</td></tr>'
        )
    return f"""<section id="second-order" aria-labelledby="second-order-heading"><h2 id="second-order-heading">6. 半潜平台的二阶差频荷载</h2>
<p>半潜平台进一步完成平均漂移与完整差频二阶势计算。采用近场表达式，包含内外自由面积分，外部积分使用 QUADPACK。水深为 200 m，浪向为 60°，波频为 0.50–1.10 rad/s，差频为 0、0.05、0.10 rad/s。原生计算覆盖 36 对有效波频，共 216 个复数荷载系数。</p>
<figure class="mesh-plate"><a href="assets/platform-second-order-mesh.png" target="_blank" rel="noopener"><img class="media-image" src="assets/platform-second-order-mesh.png" width="2400" height="1060" loading="lazy" decoding="async" alt="实际计算的半潜平台和规则环带外部积分网格"></a><figcaption>图 6a。50–110 m 的外圈采用 72 个等角分段和 9 层渐变四边形环带；近体 60° 分区按对称关系对应，水线使用湿面已有节点。主网格全体总数为 {record["main_total_panels"]:,}，包含湿面、水线面、外部自由面及对称展开；对照为 {record["comparison_total_panels"]:,}。几何倍率为 1，坐标单位为 m。</figcaption></figure>
<p>外部积分域已经检查完整覆盖、重叠、水线共边、内部接缝和面元形状，并从原生网格数据库独立核对实际使用的面元与向下法向。主网格外部自由面的内角范围为 {surface["panel_quality"]["min_corner_deg"]:.1f}°–{surface["panel_quality"]["max_corner_deg"]:.1f}°，最大边长比为 {surface["panel_quality"]["max_edge_ratio"]:.2f}。原有湿面和物理参数保持一致，一阶复响应与原算例在共同频率上逐项一致。</p>
{figures[0]}{figures[1]}
<details><summary>查看复数荷载及积分网格敏感性</summary>{figures[2]}{figures[3]}</details>
<div class="table-wrap"><table><caption>两档外部积分网格的复数差异，以各分量自身峰值归一</caption><thead><tr><th scope="col">荷载分量</th><th scope="col">最大复数差异</th><th scope="col">本例验收范围</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p>QTF 对角项与平均漂移荷载的最大归一差异为 0.032%。三个力分量及横摇、纵摇力矩通过本例的外部积分网格敏感性门限。艏摇力矩的自身峰值归一差异为 23.37%，近远场平均漂移差异为 128.85%，该分量保留作数值研究，完成进一步收敛验证后再用于工程荷载。当前比较固定湿面和外部域半径；目标工程用途需补充对应的空间、外部域、频率及参考结果证据。</p>
<p class="data-links"><a href="https://github.com/lightninnng/hydrostar-mcp/blob/main/docs/second-order.md">方法与复算说明</a>介绍完整差频计算和有效配对；<a href="https://github.com/lightninnng/hydrostar-mcp/tree/main/examples/second-order/platform">原生二阶计算包</a>提供网格、物理参数、荷载输入、复数输出与八阶段日志。前面四种构型的动画展示各自的一阶压力、波面和运动。</p></section>"""
