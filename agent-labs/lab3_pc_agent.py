"""에이전트 실습 3. 내 PC 제어 에이전트 (Windows)

자연어로 PC 상태를 점검하고, 파일을 찾고, 폴더를 정리하고, 프로그램·웹페이지를 엽니다.
조회는 바로 실행하고, PC를 바꾸는 작업은 미리보기 → 사람 승인 → 실행 순서로만 합니다.

안전장치
  - 파일 작업은 사용자 홈 폴더(C:\\Users\\<나>) 안으로 제한
  - 삭제 도구는 아예 주지 않음 (정리는 '이동'만)
  - PowerShell 명령은 승인 필수, 시스템 변경 명령은 차단 목록으로 거부

실행
  python lab3_pc_agent.py
  python lab3_pc_agent.py "다운로드 폴더를 확장자별로 정리하는 계획을 보여주고, 승인하면 실행해라"
  python lab3_pc_agent.py "C 드라이브 여유 공간과 메모리를 가장 많이 쓰는 프로그램 5개를 알려줘"
"""
import json
import os
import platform
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from agent_core import Tool, parse_cli, run_agent

HOME = Path.home().resolve()
BLOCKED = re.compile(
    r"\b(Remove-Item|rm|del|rmdir|Format-|Clear-Disk|Stop-Computer|Restart-Computer|Set-ExecutionPolicy|"
    r"reg\s+delete|Remove-ItemProperty|New-LocalUser|Add-LocalGroupMember|Disable-|Invoke-WebRequest|iwr|curl|"
    r"Invoke-Expression|iex|Start-BitsTransfer|bcdedit|vssadmin|cipher|takeown|icacls)\b",
    re.IGNORECASE,
)


def _in_home(path: str) -> Path:
    p = Path(os.path.expandvars(os.path.expanduser(path))).resolve()
    if p != HOME and HOME not in p.parents:
        raise PermissionError(f"홈 폴더({HOME}) 밖은 다룰 수 없습니다: {p}")
    return p


def _ps(command: str) -> str:
    done = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip() or f"exit={done.returncode}")
    return done.stdout.strip()


# ---- 조회 ----
def system_info() -> dict:
    total, used, free = shutil.disk_usage(HOME.anchor)
    mem = _ps("$o=Get-CimInstance Win32_OperatingSystem; '{0},{1}' -f $o.TotalVisibleMemorySize,$o.FreePhysicalMemory")
    total_kb, free_kb = (int(x) for x in mem.split(","))
    return {
        "OS": f"{platform.system()} {platform.release()} ({platform.version()})",
        "컴퓨터": platform.node(), "CPU 코어": os.cpu_count(),
        "메모리": f"{(total_kb - free_kb) / 1048576:.1f} / {total_kb / 1048576:.1f} GB 사용",
        f"{HOME.anchor} 드라이브": f"여유 {free / 1e9:.1f} GB / 전체 {total / 1e9:.1f} GB",
    }


def top_processes(sort_by: str = "memory", count: int = 10) -> str:
    key = "WorkingSet64" if sort_by == "memory" else "CPU"
    return _ps(f"Get-Process | Sort-Object {key} -Descending | Select-Object -First {int(count)} "
               "Name,Id,@{n='MemMB';e={[int]($_.WorkingSet64/1MB)}},@{n='CPUsec';e={[int]$_.CPU}} | Format-Table -AutoSize | Out-String -Width 120")


def find_files(folder: str = "~", pattern: str = "*", newer_than_days: int = 0, limit: int = 50) -> list:
    root = _in_home(folder)
    cutoff = datetime.now().timestamp() - newer_than_days * 86400 if newer_than_days else 0
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 숨김 폴더와 AppData는 건너뛴다 (느리고 시스템 파일이 많음)
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("AppData", "node_modules")]
        for name in filenames:
            p = Path(dirpath) / name
            if not p.match(pattern):
                continue
            st = p.stat()
            if st.st_mtime < cutoff:
                continue
            out.append({"path": str(p), "KB": st.st_size // 1024, "수정": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")})
            if len(out) >= limit:
                return out
    return out


def folder_summary(folder: str = "~/Downloads") -> dict:
    root = _in_home(folder)
    stats: dict = {}
    for p in root.iterdir():
        if p.is_file():
            ext = p.suffix.lower() or "(없음)"
            s = stats.setdefault(ext, {"개수": 0, "MB": 0.0})
            s["개수"] += 1
            s["MB"] = round(s["MB"] + p.stat().st_size / 1e6, 1)
    return dict(sorted(stats.items(), key=lambda kv: -kv[1]["개수"]))


# ---- 변경 (승인 필요) ----
CATEGORIES = {
    "문서": {".pdf", ".hwp", ".hwpx", ".doc", ".docx", ".txt", ".md"},
    "표·발표": {".xls", ".xlsx", ".csv", ".ppt", ".pptx"},
    "이미지": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"},
    "압축": {".zip", ".7z", ".rar", ".tar", ".gz"},
    "설치파일": {".exe", ".msi", ".apk"},
    "영상·음성": {".mp4", ".mov", ".avi", ".mp3", ".wav"},
    "코드": {".py", ".js", ".html", ".css", ".json", ".ipynb"},
}


def _plan(root: Path) -> list[tuple[Path, Path]]:
    moves = []
    for p in root.iterdir():
        if not p.is_file():
            continue
        cat = next((c for c, exts in CATEGORIES.items() if p.suffix.lower() in exts), "기타")
        dest = root / cat / p.name
        n = 1
        while dest.exists():
            dest = root / cat / f"{p.stem} ({n}){p.suffix}"
            n += 1
        moves.append((p, dest))
    return moves


def preview_organize(folder: str = "~/Downloads") -> str:
    moves = _plan(_in_home(folder))
    lines = [f"{s.name}  →  {d.parent.name}/" for s, d in moves[:80]]
    return f"총 {len(moves)}개 파일 이동 예정 (삭제 없음)\n" + "\n".join(lines)


def organize_folder(folder: str = "~/Downloads") -> str:
    root = _in_home(folder)
    moves = _plan(root)
    log = root / f"정리기록_{datetime.now():%Y%m%d_%H%M%S}.json"
    for src, dst in moves:
        dst.parent.mkdir(exist_ok=True)
        shutil.move(src, dst)
    log.write_text(json.dumps([[str(s), str(d)] for s, d in moves], ensure_ascii=False, indent=1), encoding="utf-8")
    return f"{len(moves)}개 이동 완료. 되돌리기 기록: {log}"


def open_target(target: str) -> str:
    if not re.match(r"^https?://", target):
        target = str(_in_home(target)) if any(c in target for c in "\\/~") else target
    os.startfile(target)  # URL, 파일, 또는 notepad·calc 같은 프로그램
    return f"열기: {target}"


def run_powershell(command: str) -> str:
    if BLOCKED.search(command):
        raise PermissionError("삭제·시스템 설정 변경·외부 다운로드 명령은 이 실습에서 차단됩니다.")
    return _ps(command)[:10000]


S = {"type": "string"}
TOOLS = [
    Tool("system_info", "OS, CPU, 메모리, 디스크 여유 공간을 조회한다.", {}, system_info),
    Tool("top_processes", "메모리 또는 CPU를 많이 쓰는 프로세스를 조회한다.",
         {"sort_by": {"type": "string", "enum": ["memory", "cpu"]}, "count": {"type": "integer"}}, top_processes),
    Tool("find_files", "홈 폴더 아래에서 파일을 찾는다. pattern 예: *.hwp, 보고서*",
         {"folder": S, "pattern": S, "newer_than_days": {"type": "integer"}, "limit": {"type": "integer"}}, find_files),
    Tool("folder_summary", "폴더 안 파일을 확장자별 개수·용량으로 요약한다.", {"folder": S}, folder_summary),
    Tool("preview_organize", "폴더 정리 계획(확장자별 하위 폴더로 이동)을 미리 본다. 실제로 옮기지 않는다.", {"folder": S}, preview_organize),
    Tool("organize_folder", "preview_organize 계획대로 파일을 이동한다. 삭제는 하지 않고 되돌리기 기록을 남긴다.",
         {"folder": S}, organize_folder, risky=True),
    Tool("open_target", "웹 주소, 파일, 또는 프로그램(notepad, calc, explorer 등)을 연다.", {"target": S},
         open_target, required=("target",), risky=True),
    Tool("run_powershell", "조회용 PowerShell 명령을 실행한다. 다른 도구로 안 될 때만 쓴다.", {"command": S},
         run_powershell, required=("command",), risky=True),
]

SYSTEM = f"""당신은 사용자의 Windows PC를 관리하는 비서 에이전트입니다. 사용자 홈: {HOME}
원칙:
- 조회 도구로 먼저 확인하고, 변경 작업은 반드시 미리보기(preview_organize 등)를 보여준 뒤 실행한다.
- 파일을 삭제하지 않는다. 정리는 이동으로만 하고 되돌리는 방법을 알려준다.
- 보안 설정, 계정, 네트워크 설정은 바꾸지 않는다. 필요하면 사람이 할 절차만 안내한다.
- 결과는 한국어로, 숫자와 근거를 들어 간결하게 보고한다."""

DEFAULT_GOAL = "내 PC 상태(디스크, 메모리, 무거운 프로그램)를 점검하고 다운로드 폴더 정리 계획을 미리보기로 보여줘. 실행은 하지 마."

if __name__ == "__main__":
    goal, auto_yes = parse_cli(DEFAULT_GOAL)
    print(run_agent(goal, TOOLS, SYSTEM, auto_yes=auto_yes))
