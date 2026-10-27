"""Deterministic input generation, mesh/RAO inspection and process execution.

This module uses only the standard library. All geometry quantities describe the
wetted mesh; they do not determine the physical centre of gravity or inertia.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, field

DEFAULT_ROOT = r"D:\Bureau Veritas\Hstar4Experts\v8.2.0"
RECOMMENDED_MAX_PANELS = 3000
MODULES = ("hsmsh", "hslec", "hschk", "hsrdf", "hsmcn", "hsrao", "mpiexec")
POSTPROCESS_MODULES = ("hsprs",)
DOFS = ("surge", "sway", "heave", "roll", "pitch", "yaw")
NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"


def number(value):
    result = float(str(value).replace("D", "E").replace("d", "e"))
    if not math.isfinite(result):
        raise ValueError("数值必须有限")
    return result


def positive(value, name):
    result = number(value)
    if isinstance(value, bool) or result <= 0:
        raise ValueError(f"{name} 必须大于 0")
    return result


def cells(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} 必须是正整数")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_-]{0,47}", value
    ):
        raise ValueError(
            "标识符须以字母开头，只含字母、数字、下划线或短横线，最多 48 字符"
        )
    if re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", value):
        raise ValueError("不能使用 Windows 保留名称")
    return value


def hstar_root():
    return os.environ.get("HSTAR_PATH7", DEFAULT_ROOT)


def hstar_bin(name):
    if name not in (*MODULES, *POSTPROCESS_MODULES):
        raise ValueError(f"不允许的模块: {name}")
    for sub in ("bin", "PythonWrap"):
        path = Path(hstar_root()) / sub / (name + ".exe")
        if path.is_file():
            return str(path.resolve())
    raise FileNotFoundError(f"找不到模块 {name}，请检查 HSTAR_PATH7")


@dataclass
class RunResult:
    module: str
    rc: int
    log: str
    seconds: float
    cmd: list = field(default_factory=list)
    error_code: str | None = None
    log_path: str | None = None

    @property
    def ok(self):
        return self.rc == 0 and self.error_code is None


def log_error(log):
    """Some Fortran modules report a fatal error and still exit with code 0."""
    patterns = (
        (
            "LICENSE_UNAVAILABLE",
            r"all licen[cs]es in use|running demo version|licen[cs]e.*(?:denied|expired|not found|error|unavailable)|no valid licen[cs]e",
        ),
        (
            "FORTRAN_ERROR",
            r"forrtl:\s*(?:severe|error)|fatal error|floating invalid|segmentation fault",
        ),
        (
            "INPUT_ERROR",
            r"\[ERROR\]|can't find (?:the )?input file|cannot open.*file|\*{3}\s*(?:error|can't|cannot)",
        ),
        (
            "SOLVER_EQUILIBRIUM_FAILED",
            r"(?:the ship|the body)\s+is\s+not\s+balanced",
        ),
        (
            "SOLVER_CONVERGENCE_FAILED",
            r"failed to converge|did not converge|not converged",
        ),
        (
            "INTERACTIVE_INPUT_REQUIRED",
            r"Fortran Pause|press (?:enter|return) to continue",
        ),
    )
    return next(
        (code for code, pattern in patterns if re.search(pattern, log, re.I)), None
    )


def _scan_log(path):
    """Scan every part of a log with bounded memory."""
    context = ""
    with Path(path).open("rb") as stream:
        while chunk := stream.read(65536):
            context = context[-4096:] + chunk.decode("utf-8", "replace")
            issue = log_error(context)
            if issue:
                return issue
    return None


class _WindowsJob:
    """Keep owned descendants in a kill-on-close Job Object, including MPI workers.

    taskkill /T cannot reliably enumerate children inside some desktop sandboxes.
    A nested Job Object controls descendants through the kernel instead.
    """

    def __init__(self, proc):
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_longlong),
                ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD),
                ("min_ws", ctypes.c_size_t),
                ("max_ws", ctypes.c_size_t),
                ("active", wintypes.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [
                (name, ctypes.c_ulonglong)
                for name in (
                    "read_ops",
                    "write_ops",
                    "other_ops",
                    "read_bytes",
                    "write_bytes",
                    "other_bytes",
                )
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("basic", BasicLimits),
                ("io", IoCounters),
                ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t),
                ("peak_job_memory", ctypes.c_size_t),
            ]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
        self.api.CreateJobObjectW.restype = wintypes.HANDLE
        self.api.SetInformationJobObject.argtypes = (
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        )
        self.api.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
        self.api.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
        self.api.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        self.api.CloseHandle.argtypes = (wintypes.HANDLE,)
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ) or not self.api.AssignProcessToJobObject(self.handle, int(proc._handle)):
            error = ctypes.get_last_error()
            self.api.CloseHandle(self.handle)
            self.handle = None
            raise ctypes.WinError(error)

    def terminate(self):
        if self.handle:
            self.api.TerminateJobObject(self.handle, 1)
            self.api.WaitForSingleObject(self.handle, 8000)

    def close(self):
        if self.handle:
            self.terminate()
            self.api.CloseHandle(self.handle)
            self.handle = None


def _stop_tree(proc, job=None):
    if job is not None:
        job.terminate()
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=8)
        return
    if proc.poll() is not None:
        return
    if os.name == "nt":
        # The PID belongs to this exact Popen instance; never kill by image name.
        taskkill = (
            Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/taskkill.exe"
        )
        try:
            subprocess.run(
                [str(taskkill), "/PID", str(proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if proc.poll() is None:
        proc.kill()
    proc.wait(timeout=8)


def run(module, args, cwd, nproc=0, timeout=1800, *, log_path=None, cancel=None):
    """Run without a shell, capture full logs and stop promptly on license/PAUSE.

    Each invocation must have an isolated cwd. Logs go to disk rather than an
    unbounded pipe, so an EOF/PAUSE loop cannot exhaust the MCP server's RAM.
    """
    start = time.monotonic()
    positive(timeout, "timeout")
    if isinstance(nproc, bool) or not isinstance(nproc, int) or nproc < 0:
        raise ValueError("nproc 必须是非负整数")
    workdir = Path(cwd).resolve()
    install = Path(hstar_root()).resolve()
    if workdir == install or install in workdir.parents:
        raise ValueError("禁止在 HydroStar 安装目录运行")
    cmd = []
    temporary = None
    keep_log = False
    try:
        exe = hstar_bin(module)
        cmd = [exe] + [str(a) for a in args]
        if nproc > 1:
            cmd = [
                hstar_bin("mpiexec"),
                "-n",
                str(nproc),
                "-localonly",
                "-delegate",
            ] + cmd
        if log_path is None:
            temporary = tempfile.NamedTemporaryFile(
                prefix="hs-log-", suffix=".log", dir=workdir, delete=False
            )
            temporary.close()
            destination = Path(temporary.name)
        else:
            destination = Path(log_path).resolve()
            if not destination.is_relative_to(workdir):
                raise ValueError("日志路径必须位于运行目录内")
            destination.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ)
        env["HSTAR_PATH7"] = str(install)
        env["PATH"] = os.pathsep.join(
            (str(install / "bin"), str(install / "PythonWrap"), env.get("PATH", ""))
        )
        flags = (
            {"creationflags": subprocess.CREATE_NO_WINDOW}
            if os.name == "nt"
            else {"start_new_session": True}
        )
        reason = None
        scan_offset = 0
        scan_context = ""
        with destination.open("wb") as output:
            proc = subprocess.Popen(
                cmd,
                cwd=workdir,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                env=env,
                **flags,
            )
            job = None
            try:
                if os.name == "nt":
                    job = _WindowsJob(proc)
                while proc.poll() is None:
                    if cancel is not None and cancel.is_set():
                        reason = "CANCELLED"
                    elif time.monotonic() - start > timeout:
                        reason = "TIMEOUT"
                    else:
                        with destination.open("rb") as current:
                            current.seek(scan_offset)
                            chunk = current.read(65536)
                            scan_offset = current.tell()
                        scan_context = scan_context[-4096:] + chunk.decode(
                            "utf-8", "replace"
                        )
                        reason = log_error(scan_context)
                        if destination.stat().st_size > 32 * 1024 * 1024:
                            reason = reason or "LOG_LIMIT_EXCEEDED"
                    if reason:
                        _stop_tree(proc, job)
                        break
                    if cancel is not None:
                        cancel.wait(0.1)
                    else:
                        time.sleep(0.1)
                rc = proc.wait()
            finally:
                if proc.poll() is None:
                    _stop_tree(proc, job)
                if job is not None:
                    job.close()
        with destination.open("rb") as log_file:
            prefix = log_file.read(65536)
            if destination.stat().st_size > 131072:
                log_file.seek(-65536, os.SEEK_END)
                content = prefix + b"\n[... full log on disk ...]\n" + log_file.read()
            else:
                log_file.seek(0)
                content = log_file.read()
        log = content.decode("utf-8", "replace")
        reason = (
            reason
            or (
                "LOG_LIMIT_EXCEEDED"
                if destination.stat().st_size > 32 * 1024 * 1024
                else None
            )
            or _scan_log(destination)
            or ("PROCESS_FAILED" if rc else None)
        )
        keep_log = reason is not None
        return RunResult(
            module,
            rc,
            log,
            time.monotonic() - start,
            cmd,
            reason,
            str(destination) if log_path is not None or keep_log else None,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return RunResult(
            module,
            -1,
            str(exc),
            time.monotonic() - start,
            cmd,
            "EXECUTABLE_NOT_FOUND"
            if isinstance(exc, FileNotFoundError)
            else "EXECUTION_ERROR",
        )
    finally:
        if temporary is not None and not keep_log:
            try:
                Path(temporary.name).unlink(missing_ok=True)
            except PermissionError:
                pass  # Preserve diagnostic evidence instead of masking the original failure.


def wave_limit(edge, depth="INF", gravity=9.81):
    """Screening criterion lambda >= 8*max_edge, using finite-depth dispersion."""
    edge = positive(edge, "edge")
    k = 2 * math.pi / (8 * edge)
    factor = 1.0 if depth == "INF" else math.tanh(k * positive(depth, "depth"))
    return math.sqrt(positive(gravity, "gravity") * k * factor)


def budget_barge(L, B, T, nL, nB, nT, sym=1, depth="INF", gravity=9.81):
    L, B, T = (positive(v, k) for k, v in (("L", L), ("B", B), ("T", T)))
    nL, nB, nT = (cells(v, k) for k, v in (("nL", nL), ("nB", nB), ("nT", nT)))
    if sym != 1:
        raise ValueError("箱体生成器当前只支持 SYMMETRY 1；不允许将半体标为全体")
    half = nL * nB + nL * nT + 2 * nB * nT
    area = (2 * T + B) * L + 2 * B * T
    mean = math.sqrt(area / (2 * half))
    edge = max(L / nL, B / (2 * nB), T / nT)
    omega = wave_limit(edge, depth, gravity)
    return dict(
        half=half,
        full=2 * half,
        s_wet=area,
        a=mean,
        max_edge=edge,
        waterplane_reference_full=2 * nL * nB,
        max_aspect_ratio=max(L / nL, B / (2 * nB), T / nT)
        / min(L / nL, B / (2 * nB), T / nT),
        lambda_min=8 * edge,
        omega_max=omega,
        period_min=2 * math.pi / omega,
        criterion="lambda >= 8 * max_panel_edge; screening only, convergence still required",
    )


def assess_budget(bud, recommended_max=RECOMMENDED_MAX_PANELS, wp_factor=1.2):
    cells(recommended_max, "recommended_max")
    if number(wp_factor) < 1:
        raise ValueError("wp_factor 必须 >= 1")
    # The measured corrected barge has much more than a 20% waterplane overhead.
    # Use the rectangular top-grid reference as well as the configurable factor;
    # neither is a guaranteed bound on hslec's automatic waterplane mesher.
    estimate = max(
        math.ceil(bud["full"] * wp_factor),
        bud["full"] + bud.get("waterplane_reference_full", 0),
    )
    exceeded = estimate > recommended_max
    return dict(
        status="needs_confirmation" if exceeded else "ok",
        n_hull_full=bud["full"],
        n_effective_estimate=estimate,
        n_waterplane_estimate_full=estimate - bud["full"],
        estimate_source="max(configured factor, rectangular waterplane reference where available); verify with hslec",
        recommended_max=recommended_max,
        omega_max_this_mesh=bud["omega_max"],
        message=f"全体船体 {bud['full']}，含水线面估算 {estimate}；本次预算 {recommended_max}，常规默认预算 {RECOMMENDED_MAX_PANELS}，超出本次预算时须审阅确认。",
        options=(
            [
                {"id": "revise", "label": "修改分段数后重新规划"},
                {"id": "proceed", "label": "确认面板开销后保持输入继续"},
                {"id": "cancel", "label": "取消"},
            ]
            if exceeded
            else []
        ),
    )


def _write(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")
    return str(path)


def write_mri_barge(
    path,
    L,
    B,
    T,
    nL,
    nB,
    nT,
    sym=1,
    rule_bottom=0,
    rule_side=0,
    rule_top=0,
    project="BARGE",
):
    budget_barge(L, B, T, nL, nB, nT, sym)
    identifier(project)
    if any(x != 0 for x in (rule_bottom, rule_side, rule_top)):
        raise ValueError("当前模板只定义 RULE 0，不能引用未定义的加密规则")
    hl, hb = L / 2, B / 2
    nodes = {
        1: (-hl, 0, -T),
        2: (-hl, hb, -T),
        3: (-hl, hb, 0),
        4: (-hl, 0, 0),
        5: (hl, 0, -T),
        6: (hl, hb, -T),
        7: (hl, hb, 0),
        8: (hl, 0, 0),
    }
    # AB/BC follow the actual A->B and B->C edges, NOT a fixed x/y order.
    patches = [
        ("bottom", (1, 2, 6, 5), nB, nL),
        ("side", (2, 3, 7, 6), nT, nL),
        ("aft", (1, 4, 3, 2), nT, nB),
        ("fore", (5, 6, 7, 8), nB, nT),
    ]
    lines = ["TYPE 1", f"SYMMETRY {sym}", "ZFSURFACE 0.0", f"# project: {project}"]
    lines += [f"NODE {i} {x:.9g} {y:.9g} {z:.9g}" for i, (x, y, z) in nodes.items()]
    lines.append("RULE 0 0.0 0.0")
    for i, (name, panel, ab, bc) in enumerate(patches, 1):
        lines += [
            f"# {name}",
            f"PATCH {i} NODE {' '.join(map(str, panel))} AB_NB {ab} AB_RULE 0 BC_NB {bc} BC_RULE 0",
        ]
    return _write(path, "\n".join(lines + ["ENDFILE", ""]))


def build_mesh(workdir, project, mri_path):
    identifier(project)
    workdir = Path(workdir).resolve()
    mri = Path(mri_path).resolve()
    if mri.parent != workdir:
        raise ValueError("MRI 必须在当前独立运行目录内")
    source, destination = workdir / "PRO.hst", workdir / (project + ".hst")
    if source.exists() or destination.exists():
        raise FileExistsError("发现已有网格；请使用新的独立运行目录，防止读取旧文件")
    result = run(
        "hsmsh", [mri.name], workdir, timeout=60, log_path=workdir / "logs/hsmsh.log"
    )
    if not result.ok or not source.is_file() or source.stat().st_size == 0:
        if result.ok:
            result.error_code = "MISSING_ARTIFACT"
        return result, None
    source.replace(destination)
    return result, str(destination)


def grid_values(start, stop, step, *, name="grid", max_count=10000):
    start, stop, step = number(start), number(stop), positive(step, "step")
    if stop < start:
        raise ValueError(f"{name}: max 必须 >= min")
    intervals = (stop - start) / step
    if not math.isclose(intervals, round(intervals), abs_tol=1e-7, rel_tol=1e-9):
        raise ValueError(f"{name}: (max-min) 必须是 step 的整数倍，避免隐式改变区间")
    count = round(intervals) + 1
    if count > max_count:
        raise ValueError(f"{name}: 点数 {count} 超出允许的 {max_count}")
    return [start + i * step for i in range(count)]


def write_rdf(
    path,
    rdf_name="rd1",
    wmin=0.05,
    wmax=1.8,
    wstp=0.05,
    hmin=0.0,
    hmax=360.0,
    hstp=30.0,
    depth="INF",
    speeds=((1, 0.0),),
    extra="",
):
    identifier(rdf_name)
    positive(wmin, "wmin")
    grid_values(wmin, wmax, wstp, name="frequency")
    grid_values(hmin, hmax, hstp, name="heading", max_count=361)
    if hmin < 0 or hmax > 360:
        raise ValueError("浪向范围须在 0..360 度")
    if depth != "INF":
        positive(depth, "depth")
    if len(speeds) != 1 or speeds[0][0] != 1 or number(speeds[0][1]) < 0:
        raise ValueError("当前结果回读支持一个非负航速")
    if extra.strip():
        raise ValueError("不接受任意文本注入；请扩展结构化输入字段")
    return _write(
        path,
        f"""# omega: rad/s; heading: propagation angle from +x (0 following, 180 head seas)
FILENAME {rdf_name}
FREQUENCY TYPE 2
WMIN {wmin:.10g}
WMAX {wmax:.10g}
WSTP {wstp:.10g}
ENDFREQUENCY
HEADING TYPE 2
HMIN {hmin:.10g}
HMAX {hmax:.10g}
HSTP {hstp:.10g}
ENDHEADING
WATERDEPTH {depth}
SPEEDS TYPE 0
1 {speeds[0][1]:.10g}
ENDSPEEDS
ENDFILE
""",
    )


def validate_passive_matrix(matrix):
    """Finite symmetric PSD 6x6 matrix; diagonal scaling preserves mixed SI units."""
    if len(matrix) != 6 or any(len(row) != 6 for row in matrix):
        raise ValueError("线性阻尼矩阵必须为 6x6")
    a = [[number(v) for v in row] for row in matrix]
    if any(a[i][i] < 0 for i in range(6)):
        raise ValueError("线性阻尼矩阵须为半正定")
    for i in range(6):
        for j in range(6):
            if not math.isclose(a[i][j], a[j][i], rel_tol=1e-10, abs_tol=1e-12):
                raise ValueError("线性阻尼矩阵须对称")
            if (a[i][i] == 0 or a[j][j] == 0) and a[i][j] != 0:
                raise ValueError("零阻尼对角项对应的耦合项须为零")
    scaled = [
        [
            a[i][j] / math.sqrt(a[i][i] * a[j][j]) if a[i][i] * a[j][j] else 0.0
            for j in range(6)
        ]
        for i in range(6)
    ]
    for k in range(6):
        pivot = scaled[k][k]
        if pivot < -1e-9 or (
            abs(pivot) <= 1e-9
            and any(abs(scaled[i][k]) > 1e-8 for i in range(k + 1, 6))
        ):
            raise ValueError("线性阻尼矩阵须为半正定")
        if pivot > 1e-9:
            for i in range(k + 1, 6):
                for j in range(k + 1, 6):
                    scaled[i][j] -= scaled[i][k] * scaled[k][j] / pivot
    return a


def write_mcn(
    path,
    rdf_name="rd1",
    mass=1.0,
    cog=(0, 0, 0),
    gyradius=(0, 0, 0, 0, 0, 0),
    roll_damp_pct=None,
    extra="",
    *,
    rho=1025.0,
    gravity=9.81,
    stiffness_matrix=None,
    linear_damping_matrix=None,
    waterplane_hydrostatics=False,
    morison=(),
    wave_amplitude=None,
    spectrum=None,
):
    identifier(rdf_name)
    positive(mass, "mass")
    if len(cog) != 3 or len(gyradius) != 6:
        raise ValueError("COG 需要 3 个数，GYRADIUS 需要 6 个数")
    validate_gyradius(gyradius)
    if extra.strip():
        raise ValueError("不接受任意 MCN 文本注入")
    rows = [
        f"FILENAME {rdf_name}",
        f"RHO {positive(rho, 'rho'):.12g}",
        f"GRAVITY {positive(gravity, 'gravity'):.12g}",
        f"MASS_BODY 1 {mass:.12g}",
        "COGPOINT_BODY 1 " + " ".join(f"{number(x):.12g}" for x in cog),
        "GYRADIUS_BODY 1 " + " ".join(f"{number(x):.12g}" for x in gyradius),
    ]
    if waterplane_hydrostatics:
        rows.append("HYDSWPLANE")
    if roll_damp_pct is not None:
        if number(roll_damp_pct) < 0:
            raise ValueError("阻尼百分比不能为负")
        rows.append(f"LINVISCOUSDAMPING 1 {roll_damp_pct:.10g}")
    if stiffness_matrix is not None:
        if len(stiffness_matrix) != 6 or any(len(row) != 6 for row in stiffness_matrix):
            raise ValueError("刚度矩阵必须为 6x6")
        rows += ["STIFFNESS_MATRIX TYPE 0 BODY 1 1"]
        rows += [" ".join(f"{number(v):.12g}" for v in row) for row in stiffness_matrix]
        rows.append("ENDSTIFFNESS_MATRIX")
    if linear_damping_matrix is not None:
        validate_passive_matrix(linear_damping_matrix)
        rows.append("DAMPING_MATRIX TYPE 0 BODY 1")
        rows += [
            " ".join(f"{number(v):.12g}" for v in row) for row in linear_damping_matrix
        ]
        rows.append("ENDDAMPING_MATRIX")
    if morison:
        if (
            any(m["cd"] > 0 for m in morison)
            and wave_amplitude is None
            and spectrum is None
        ):
            raise ValueError("有 Cd 的 Morison 杆件必须显式指定阻力线性化海况")
        rows.append("MORISON")
        for i, member in enumerate(morison, 1):
            values = [
                *member["start"],
                *member["end"],
                member["diameter"],
                member["cm"],
                member["cd"],
            ]
            rows.append(
                f"{i} CIRC "
                + " ".join(f"{number(v):.12g}" for v in values)
                + f" {cells(member['segments'], 'segments')}"
            )
        rows.append("ENDMORISON")
    if wave_amplitude is not None:
        rows.append(f"WAVEAMPLITUDE {positive(wave_amplitude, 'wave_amplitude'):.10g}")
    if spectrum is not None:
        rows += [
            "STOCHASTIC_MORISON",
            "JONSWAP HS {hs:.10g} TP {tp:.10g} GAMMA {gamma:.10g} RELHEAD {heading:.10g} NO".format(
                **spectrum
            ),
            "ENDSTOCHASTIC_MORISON",
        ]
    return _write(path, "\n".join(rows + ["ENDFILE", ""]))


def write_rao(path, dofs=DOFS, rdf_name="rd1", ref=None):
    if not dofs or len(set(dofs)) != len(dofs) or any(d not in DOFS for d in dofs):
        raise ValueError("DOF 必须是非重复的 surge/sway/heave/roll/pitch/yaw")
    rows = [f"G{d.upper()} BODY 1 FILE {d}.rao" for d in dofs]
    if ref is not None:
        if len(ref) != 3:
            raise ValueError("参考点须为 3 个数")
        rows.append(
            "MHEAVE BODY 1 FILE heave_at_point.rao AT "
            + " ".join(f"{number(v):.10g}" for v in ref)
        )
    return _write(path, "\n".join(rows + [""]))


_CNT = {
    "zero_area": r"nb of zero-area panels",
    "over_free_surface": r"nb of panels over free surface",
    "at_free_surface": r"nb of panels at free surface",
    "superposition": r"nb of superpositions",
    "inconsistence": r"nb of inconsistences",
    "neighbor_absence": r"nb of neighbor-absences",
    "symmetry_problem": r"nb of symmetry problems?",
}


def parse_hschk(log):
    result = {}
    for key, pattern in _CNT.items():
        matches = re.findall(pattern + r"\s*=\s*(\d+)", log, re.I)
        result[key] = int(matches[0]) if len(matches) == 1 else None
    result["pass"] = all(result[k] == 0 for k in _CNT) and log_error(log) is None
    return result


def parse_hslec(log):
    result = {}
    patterns = {
        "bodies": "Nb of bodies to be analysed",
        "symmetry": "Nb symmetry of hull geometry",
        "hull_panels": "Nb panels on hulls",
        "waterline_segments": "Nb segments along waterlines",
        "waterplane_panels": "Nb panels on the waterplanes",
        "above_waterline": "Nb hull panels over the waterline",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern + r"\s*(?:=|:)?\s*(\d+)", log, re.I)
        result[key] = int(match[1]) if match else None
    match = re.search(r"center of buoyancy x=\s*(" + NUMBER + ")", log, re.I)
    result["cb_x"] = number(match[1]) if match else None
    return result


def parse_hsmcn(log):
    result = {
        "balanced": not bool(
            re.search(r"(?:the ship|the body)\s+is\s+not\s+balanced", log, re.I)
        )
    }
    match = re.search(r"Relative Error\s*=\s*(" + NUMBER + r")\s*%", log, re.I)
    result["relative_error_pct"] = number(match[1]) if match else None
    gm = re.search(
        r"GMxx\s*,\s*GMyy\s*\(\s*(" + NUMBER + r")\s*,\s*(" + NUMBER + r")\s*\)",
        log,
        re.I,
    )
    result["gm_roll_pitch_m"] = [number(gm[1]), number(gm[2])] if gm else None
    return result


def validate_gyradius(radii):
    """Check physical inertia using signed squared radii, HstarManual p.69.

    I/m must be positive definite, and the underlying second-moment tensor
    S/m = trace(I/m)/2*Identity - I/m must be positive semidefinite.
    """
    if len(radii) != 6:
        raise ValueError("请提供六个关于重心的回转半径")
    r = [number(v) for v in radii]
    if any(v <= 0 for v in r[:3]):
        raise ValueError("三个主回转半径须为正")
    a, b, c = [v * v for v in r[:3]]
    d, e, f = [math.copysign(v * v, v) for v in r[3:]]
    scale = max(a, b, c)
    a, b, c, d, e, f = [v / scale for v in (a, b, c, d, e, f)]

    def determinant(x, y, z, u, v, w):
        return x * y * z + 2 * u * v * w - x * w * w - y * v * v - z * u * u

    if a * b - d * d <= 1e-12 or determinant(a, b, c, d, e, f) <= 1e-12:
        raise ValueError("回转半径应构成正定惯性矩阵，请核对交叉项及单位")
    trace_half = (a + b + c) / 2
    x, y, z = trace_half - a, trace_half - b, trace_half - c
    if (
        min(
            x,
            y,
            z,
            x * y - d * d,
            x * z - e * e,
            y * z - f * f,
            determinant(x, y, z, -d, -e, -f),
        )
        < -1e-10
    ):
        raise ValueError("惯性参数须满足物理二阶矩约束，请核对主回转半径和交叉项")


def morison_displacement(members, free_surface=0.0):
    """Full-body slender-cylinder volume; virtual Cm=0 members add drag only.

    Centreline clipping follows the slender-member approximation. The solver's
    own equilibrium diagnostic supplies the subsequent independent check.
    """
    volume = 0.0
    moment = [0.0, 0.0, 0.0]
    physical = 0
    virtual = 0
    for member in members:
        cm = number(member["cm"])
        if cm < 0:
            raise ValueError("Cm 须为非负数")
        if cm == 0:
            virtual += 1
            continue
        a, b = [tuple(number(v) for v in member[key]) for key in ("start", "end")]
        if len(a) != 3 or len(b) != 3:
            raise ValueError("杆件端点请提供三维坐标")
        za, zb = a[2] - free_surface, b[2] - free_surface
        if abs(za) < 1e-12 and abs(zb) < 1e-12:
            raise ValueError("实体杆件轴线位于自由面，请先明确其浸没截面模型")
        fraction = 1.0
        wet_a, wet_b = a, b
        if min(za, zb) >= 0:
            fraction = 0.0
        elif max(za, zb) > 0:
            fraction = -min(za, zb) / abs(za - zb)
            t = -za / (zb - za)
            intersect = tuple(a[k] + t * (b[k] - a[k]) for k in range(3))
            wet_a, wet_b = (a, intersect) if za < 0 else (intersect, b)
        dv = (
            math.pi
            * positive(member["diameter"], "diameter") ** 2
            / 4
            * math.dist(a, b)
            * fraction
        )
        volume += dv
        for k in range(3):
            moment[k] += dv * (wet_a[k] + wet_b[k]) / 2
        physical += 1
    return dict(
        volume_m3=volume,
        cb_m=[v / volume for v in moment] if volume > 1e-12 else None,
        physical_members=physical,
        virtual_members=virtual,
        source="full-body slender circular cylinders; centreline free-surface clipping; Cm=0 excluded",
    )


def read_rao(path):
    return read_rao_text(
        Path(path).read_text(encoding="utf-8", errors="strict"), str(path)
    )


def read_rao_text(content, path="<text>"):
    """Parse the same strict native RAO format from an archived text record."""
    omega, heads, amps, phases, metadata = [], [], [], [], {}
    ended = False
    for lineno, raw in enumerate(content.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.upper().startswith("#HEADING ") or line.upper() == "#HEADING":
                if heads or omega:
                    raise ValueError(f"{path}:{lineno}: 重复的 HEADING 段")
                heads = [number(t) for t in line.split()[1:]]
            elif line.upper().startswith("#NBHEADING"):
                metadata["n_heading"] = int(line.split()[-1])
            elif ":" in line:
                key, value = line[1:].split(":", 1)
                metadata[key.strip().upper()] = value.strip()
            if line.upper().startswith("#ENDFILE"):
                ended = True
            continue
        if ended or not heads:
            raise ValueError(f"{path}:{lineno}: 无浪向表，或数据出现在 ENDFILE 后")
        values = [number(t) for t in line.split()]
        if len(values) != 1 + 2 * len(heads):
            raise ValueError(
                f"{path}:{lineno}: RAO 列数不完整，期望 {1 + 2 * len(heads)} 列"
            )
        if values[0] <= 0 or (omega and values[0] <= omega[-1]):
            raise ValueError(f"{path}:{lineno}: 频率须为正且严格递增")
        if any(v < 0 for v in values[1 : 1 + len(heads)]):
            raise ValueError(f"{path}:{lineno}: 幅值不能为负")
        omega.append(values[0])
        amps.append(values[1 : 1 + len(heads)])
        phases.append(values[1 + len(heads) :])
    if not omega or not ended or len(heads) != len(set(heads)):
        raise ValueError(f"{path}: RAO 为空、缺 ENDFILE，或浪向重复")
    if metadata.get("n_heading", len(heads)) != len(heads):
        raise ValueError("NBHEADING 与实际浪向数不一致")
    return dict(
        omega=omega,
        headings=heads,
        amplitude=amps,
        phase=phases,
        unit=metadata.get("UNIT"),
        metadata=metadata,
    )


def parse_rao(path):
    result = read_rao(path)
    return result["omega"], result["headings"], result["amplitude"], result["phase"]


def read_hst(path):
    """Strict single-body HST reader; select NUMPANEL wetted panels only.

    Reject unsupported transforms instead of returning plausible wrong volumes.
    PANEL TYPE 0 has four node IDs; TYPE 1 adds a leading panel ID.
    """
    nodes, all_panels, meta = {}, {}, {}
    section, panel_type, automatic_id = None, 0, 0
    ended = False
    for lineno, raw in enumerate(
        Path(path).read_text(encoding="utf-8-sig", errors="strict").splitlines(), 1
    ):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        tok = line.split()
        key = tok[0].upper()
        if key == "ENDFILE":
            ended = True
            break
        if key.startswith("ENDCOORDINATES") or key in ("ENDPANEL", "ENDPANELS"):
            section = None
            continue
        if key in ("COORDINATES", "PANEL", "PANELS"):
            kind = int(tok[-1]) if len(tok) >= 3 and tok[-2].upper() == "TYPE" else 0
            if kind not in ((0,) if key == "COORDINATES" else (0, 1)):
                raise ValueError(f"不支持 {key} TYPE {kind}")
            section = "coord" if key == "COORDINATES" else "panel"
            panel_type = kind
            continue
        if section == "coord":
            if len(tok) != 4 or int(tok[0]) in nodes:
                raise ValueError(f"{path}:{lineno}: 节点格式错误或编号重复")
            nodes[int(tok[0])] = tuple(number(v) for v in tok[1:])
        elif section == "panel":
            if len(tok) != 4 + panel_type:
                raise ValueError(f"{path}:{lineno}: 面板列数错误")
            automatic_id += 1
            index = int(tok[0]) if panel_type else automatic_id
            if index in all_panels:
                raise ValueError("面板编号重复")
            all_panels[index] = tuple(int(v) for v in tok[panel_type:])
        elif key in ("TRANS", "ROTA", "NODE0", "NODE0_BODY", "TRANS_BODY", "ROTA_BODY"):
            raise ValueError(f"独立积分暂不支持 {key}；请先转换到统一坐标后导入")
        elif key in (
            "SYMMETRY",
            "SYMMETRY_BODY",
            "NBBODY",
            "NUMPANEL",
            "NUMFHULL",
            "NUMFPONT",
            "NUMFSWATER",
            "RHO",
            "GRAVITY",
            "ZFSURFACE",
            "COEFZ0",
        ):
            meta.setdefault("SYMMETRY_BODY" if key == "SYMMETRY" else key, []).append(
                [number(v) for v in tok[1:]]
            )
    if not ended or not nodes or not all_panels:
        raise ValueError("HST 缺少节点、面板或 ENDFILE")
    if meta.get("NBBODY", [[1]]) != [[1]]:
        raise ValueError("当前独立积分只支持单体；多体不得按单体对称还原")
    sym_entries = meta.get("SYMMETRY_BODY", [[1, 0]])
    if (
        len(sym_entries) != 1
        or len(sym_entries[0]) != 2
        or sym_entries[0][0] != 1
        or sym_entries[0][1] not in (0, 1, 2)
    ):
        raise ValueError("SYMMETRY 必须为单体的 0、1 或 2")
    selected = []
    ranges = meta.get("NUMPANEL", meta.get("NUMFHULL"))
    if ranges is None:
        if any(key in meta for key in ("NUMFPONT", "NUMFSWATER")):
            raise ValueError("含可视化/水线面时必须提供湿表面 NUMPANEL 范围")
        selected = list(all_panels.values())
    else:
        used = set()
        for entry in ranges:
            if (
                len(entry) != 3
                or entry[0] != 1
                or any(v != int(v) for v in entry)
                or entry[1] > entry[2]
            ):
                raise ValueError("NUMPANEL 范围无效")
            for i in range(int(entry[1]), int(entry[2]) + 1):
                if i not in all_panels or i in used:
                    raise ValueError("湿表面引用缺失或重复的面板")
                selected.append(all_panels[i])
                used.add(i)
    if not selected:
        raise ValueError("湿表面为空")
    for panel in selected:
        if len(set(panel)) < 3 or any(i not in nodes for i in panel):
            raise ValueError("面板缺失节点，或少于 3 个不同节点")
    return nodes, selected, meta


def hydrostatics(hst_path):
    nodes, panels, meta = read_hst(hst_path)
    return integrate_mesh(nodes, panels, meta)


def integrate_mesh(nodes, panels, meta):
    """Integrate oriented wet panels; symmetry/free-surface cuts pass through origin."""
    sym = int(meta.get("SYMMETRY_BODY", [[1, 0]])[0][1])
    free_surface = meta.get("ZFSURFACE", [[0]])[0][0]
    volume, moment, area, max_edge, max_aspect = 0.0, [0.0] * 3, 0.0, 0.0, 1.0
    for panel in panels:
        points = [(nodes[i][0], nodes[i][1], nodes[i][2] - free_surface) for i in panel]
        if any(p[2] > 1e-6 for p in points):
            raise ValueError("湿面板位于自由面以上；请先裁剪网格")
        if sym and any(p[1] < -1e-6 for p in points):
            raise ValueError("对称半体须位于 y>=0")
        if sym == 2 and any(p[0] < -1e-6 for p in points):
            raise ValueError("双对称四分之一体须位于 x>=0,y>=0")
        lengths = [math.dist(points[i], points[(i + 1) % 4]) for i in range(4)]
        nonzero = [v for v in lengths if v > 1e-12]
        max_edge = max(max_edge, *nonzero)
        max_aspect = max(max_aspect, max(nonzero) / min(nonzero))
        panel_area = 0.0
        for ia, ib, ic in ((0, 1, 2), (0, 2, 3)):
            a, b, c = points[ia], points[ib], points[ic]
            u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
            cross = (
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0],
            )
            panel_area += math.sqrt(sum(x * x for x in cross)) / 2
            dv = (
                a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])
            ) / 6
            volume += dv
            for k in range(3):
                moment[k] += dv * (a[k] + b[k] + c[k]) / 4
        if panel_area < 1e-12:
            raise ValueError("零面积湿面板")
        area += panel_area
    if volume <= 1e-12:
        raise ValueError("排水量非正；检查法向和闭合性，不自动翻转法向")
    cb = [m / volume for m in moment]
    if sym:
        cb[1] = 0.0
    if sym == 2:
        cb[0] = 0.0
    cb[2] += free_surface
    return dict(
        volume=volume * 2**sym,
        cb=tuple(cb),
        wetted_area=area * 2**sym,
        n_nodes=len(nodes),
        n_panels=len(panels),
        sym=sym,
        max_edge=max_edge,
        max_aspect_ratio=max_aspect,
        free_surface=free_surface,
        rho=meta.get("RHO", [[1025]])[0][0],
        gravity=meta.get("GRAVITY", [[9.81]])[0][0],
    )
