# 多来源几何建模与验收

复杂几何通过统一前处理转成带来源记录的湿表面，再进入 HydroStar 的原生准备与求解链路。输入可以是型值表、CAD、剖面曲线、已有表面网格或经过标定的图纸。资料中的单位、坐标、平均水线、剖面对应关系和误差上限共同决定可重建的几何。

本流程服务于单刚体一阶频域分析。通用几何入口扩大了可表达的外形，物理模型仍按排水包络、细杆、质量、恢复和阻尼分别建立。

## 输入资料与转换方式

| 输入 | 转换方式 | 必要信息 |
| --- | --- | --- |
| JSON 剖面 | 多实体放样与加减布尔运算 | 站位轴、顺序闭合轮廓、直线或插值曲线、直纹或平顺纵向插值 |
| CSV 型值表 | 按 station 分组放样 | station,u,v 表头；m、cm 或 mm；轮廓顺序 |
| DXF | 每个指定图层读取一个闭合剖面 | station_layers、站位轴、INSUNITS 或显式单位 |
| STEP 与 IGES | OpenCASCADE 实体导入与平均水线裁剪 | 文件声明单位，units=file，闭合的外部排水实体 |
| BREP | 实体导入与显式尺度转换 | m、cm 或 mm；外部排水实体 |
| STL、OBJ、PLY | 三角形或平面四边形表面导入、裁剪与节点合并 | 显式单位、原始法向和封闭湿表面 |
| HST | 展开支持的对称信息，转成全体湿表面 | 单体网格、显式源单位、平均水线 |
| PNG、JPEG、TIFF、PDF | 渲染并建立尺寸标定与剖面描线工作区 | 同一投影的已知尺寸、独立检查尺寸、描线不确定度 |

DXF 支持闭合 LWPOLYLINE、POLYLINE、SPLINE、CIRCLE 和 ELLIPSE。X/Y 作为剖面 u/v；图层与站位的关系由使用者给出。折线保留全部原始角点和曲线离散点。折线剖面采用相同点数与特征顺序，平顺剖面可以采用不同点数。多投影视图应分别标定、解释，再汇入同一坐标系。

STEP 和 IGES 的文件单位由内核转换为米。IGES 读取先初始化内核的单位参数，再在独立模型中重新按米导入；回归测试使用原创毫米制实体核对尺寸和体积。BREP、型值表和表面网格的单位显式提供。全部坐标转换保持右手系；translation_m 与 waterline_z_m 采用目标米制坐标，转换后平均水线为 z=0。

## 从站位剖面建立曲面

多边形采用 polyline 保留折角，圆舭等平顺型线采用 spline 插值通过剖面点。CSV 和 DXF 的纵向插值由 longitudinal_ruled 控制，默认直纹；设为 false 后采用平顺放样。JSON 可为每个实体指定 ruled。

闭合曲线的参数缝影响网格布置。对于沿 x 或 y 放样的船体，可将 spline_seam 设为 lowest_z，使剖面闭合缝位于龙骨侧。源点仍完整保留，避免闭合缝在水线附近形成不必要的细长网格。该选择连同纵向平顺假设写入请求文件。

剖面至少具有三个点和有限面积。当前剖面放样以有限端剖面封闭端部；实际尖艏、尖艉或顶点收口宜先在 CAD 中形成完整实体后导入。曲率、尖角和局部细节需要与面元尺寸一起检查。mesh_size_m 控制全局尺寸，curvature_samples 控制曲率离散，短 CAD 边附近采用局部尺寸场。

JSON 示例给出带贯通开口的构造性建模：

~~~json
{
  "schema_version": 1,
  "solids": [
    {
      "name": "outer",
      "axis": "z",
      "curve": "polyline",
      "ruled": true,
      "profiles": [
        {"position": -10, "points": [[-20,-15],[20,-15],[20,15],[-20,15]]},
        {"position": 5, "points": [[-20,-15],[20,-15],[20,15],[-20,15]]}
      ]
    },
    {
      "name": "opening",
      "operation": "cut",
      "axis": "z",
      "profiles": [
        {"position": -12, "points": [[-5,-4],[5,-4],[5,4],[-5,4]]},
        {"position": 7, "points": [[-5,-4],[5,-4],[5,4],[-5,4]]}
      ]
    }
  ]
}
~~~

## 图纸尺寸标定

build_geometry 读取图像或指定 PDF 页时返回 digitization_required，并生成 drawing.png 和 digitize.html。工作区使用同一投影内至少三个不共线坐标点拟合二维仿射映射，再以至少两个不同的独立尺寸点检查。标定残差、独立检查误差均应低于明确给定的米制误差上限。

完成标定后，沿同一轮廓方向和特征顺序描绘各站位。导出的 sections.json 与对应 source 图纸放在同一输入目录，使用 units=m 再次调用 build_geometry。后端重新校验标定点、独立点、图纸快照与 SHA-256，随后执行几何验收。仿射标定适合正投影及比例、旋转、斜切修正；存在明显透视畸变的照片应先正射校正。原图的清晰度、缺失尺寸和描线不确定度记录在 source_note。

图像与 PDF 渲染、尺寸标定以及已知体积的描线数据均有后端回归测试。当前环境的浏览器策略限制本地 file 网页预览，交互描线界面的人工操作检查单独保留为待完成项。

## 几何硬性验收

前处理在独立进程运行，采用明确的时间与面元上限。验收包含有限坐标、有效索引、非零面积、重复面、湿面位置、共享边方向、水线闭环、预期连通分量以及全局三角面自交。CAD 网格法向由实体内外探针确定，再独立核对面元边的方向和正排水体积。

只有 z=0 的水线允许作为湿表面开边。贯通月池的内壁与外壳属于同一排水边界；密闭内部结构空腔应先整理成外部排水包络。多个湿体可以作为一个刚体的组成部分导入，expected_wet_components 必须与实际湿面连通分量一致。

CAD 排水体积与面元积分体积的默认相对容差为 0.5%。浮心距离容差为 max(0.002 m, 0.0005 × 最大湿体尺度)。另外可以提供目标排水体积及其容差。表面网格通过拓扑检查但缺少独立体积参照时，fidelity 明确记录为 source_reference_pending。

geometry_accepted 表示这份湿表面通过所列几何判据。后续 prepare_case 和 start_case 仍执行六项原生门禁。3000 个全体等效面元、最大边长对应的波长筛查和长宽比 5 属于建模建议，超出时保留具体数值并要求审阅。复杂几何示例显式设置每次计算的资源预算。

## 几何与水动力模型的对应关系

| 结构形式 | 适用的几何表达 | 当前物理分析范围 |
| --- | --- | --- |
| 船舶、FPSO、浮箱、沉箱 | 曲线站位、折角剖面、外形 CAD 或湿面 | 单刚体线性辐射绕射和六自由度响应 |
| 半潜、Spar、柱式与组合浮体 | 外部排水实体并集、分离湿体、升沉板 | 同一刚体；细杆可使用已支持的 Morison 分工 |
| 月池与贯通开口 | CAD 减体与内壁湿表面 | 势流几何耦合；共振与黏性耗散需专门验证和标定 |
| TLP 与约束浮体 | 同一刚体加附加线性刚度 | 当前执行条件为零静态外载；实际预张力平衡和动态张力需扩展 |
| 导管架、密集细杆与桁架 | 构件几何与 Morison 理想化 | 几何本身不能建立结构弹性与构件强度结论 |
| 多船、铰接体和柔性结构 | 可先处理各自几何资料 | 当前求解编排采用单刚体；多体及结构自由度需另行实现 |

目标对象的完整型线、装载与惯性、恢复与阻尼、网格和频率敏感性及参考响应，共同决定课程研究或工程简化分析的适用精度。

## 运行与复核

~~~powershell
python -m pip install -e ".[geometry]"
python -m hydrostar_mcp geometry-formats
python -m hydrostar_mcp geometry-inspect examples/geometry/sources/vessel-stations.csv
python -m hydrostar_mcp geometry-build examples/geometry/lofted_vessel/geometry/request.json
~~~

build_geometry 返回 case_geometry，可直接用于新的 CaseConfig.geometry，并补全 mechanics、environment 和项目名。保留 source_manifest 后，生成与准备阶段核验整个几何包，将其复制并冻结到算例目录，启动前复核 SHA-256。修改源几何后应建立新包和新算例。

[复杂几何示例](../examples/geometry)保存原创 CSV、JSON、毫米制 STEP、DXF、验收湿面、几何图、原生输入和 RAO。使用以下命令可建立并重算，求解需要本机 HydroStar 授权。三个算例的 7 个频率和 4 个浪向用于验证数据与执行链路；峰区研究应独立加密。

~~~powershell
python scripts/geometry_source_study.py --sources
python scripts/geometry_source_study.py --build --run
python scripts/export_geometry.py
python scripts/check_geometry.py
~~~

完整的现有源文件会被保留。--build 复核已有验收包及其源文件 SHA-256 后复用；每次 --run 新建原生算例。修改几何的对比研究应放在独立目录，以各自源包和配置运行。

## 技术参考

CAD 与放样接口参见 [Gmsh 官方手册](https://gmsh.info/doc/texinfo/gmsh.html)。DXF 的曲线和离散参见 [ezdxf 官方文档](https://ezdxf.readthedocs.io/en/stable/path.html)，网格格式参见 [meshio 项目文档](https://github.com/nschloe/meshio)，PDF 渲染参见 [pypdfium2 文档](https://pypdfium2.readthedocs.io/en/stable/)。这些软件提供几何或文件处理能力，工程结论由具体模型的验证支持。

[返回 README](../README.md)　[建模与质量检查](modeling-guide.md)
