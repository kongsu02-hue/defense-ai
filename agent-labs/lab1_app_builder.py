"""에이전트 실습 1. 앱 개발 에이전트

요구사항을 주면 에이전트가 파일을 만들고, 테스트를 돌리고, 실패하면 고쳐서 앱을 완성합니다.
Claude Code 같은 'AI 코딩 에이전트'가 내부에서 하는 일을 80줄로 직접 구현해 봅니다.

안전장치
  - 모든 파일 작업은 workspace/ 폴더 안으로 제한 (밖으로 나가는 경로는 거부)
  - 명령 실행은 허용 목록(python, pytest, node, npm)만, 매번 사람 승인

실행
  python lab1_app_builder.py
  python lab1_app_builder.py "정비 요청 접수 웹앱을 만들어라. 단일 index.html, localStorage 저장, 상태별 필터"
  python lab1_app_builder.py --yes "..."     # 명령 실행 자동 승인 (실습용 PC에서만)
"""
import shlex
import subprocess
import sys
from pathlib import Path

from agent_core import Tool, parse_cli, run_agent

WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)
ALLOWED_COMMANDS = {"python", "pytest", "node", "npm"}


def _safe(path: str) -> Path:
    p = (WORKSPACE / path).resolve()
    if p != WORKSPACE.resolve() and WORKSPACE.resolve() not in p.parents:
        raise PermissionError(f"workspace 밖 경로는 접근할 수 없습니다: {path}")
    return p


def list_files(path: str = ".") -> str:
    root = _safe(path)
    files = [str(p.relative_to(WORKSPACE)) for p in sorted(root.rglob("*"))
             if p.is_file() and "__pycache__" not in p.parts and ".pytest_cache" not in p.parts]
    return "\n".join(files) or "(비어 있음)"


def read_file(path: str) -> str:
    return _safe(path).read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"{path} 저장 ({len(content.splitlines())}줄)"


def run_command(command: str) -> str:
    argv = shlex.split(command, posix=False)
    if not argv or argv[0] not in ALLOWED_COMMANDS:
        raise PermissionError(f"허용된 명령만 실행할 수 있습니다: {sorted(ALLOWED_COMMANDS)}")
    if argv[0] == "python":
        argv[0] = sys.executable
    elif argv[0] == "pytest":
        argv = [sys.executable, "-m", "pytest", *argv[1:]]
    done = subprocess.run(argv, cwd=WORKSPACE, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    return f"exit={done.returncode}\n{done.stdout[-6000:]}\n{done.stderr[-3000:]}"


TOOLS = [
    Tool("list_files", "workspace 안의 파일 목록을 본다.",
         {"path": {"type": "string", "description": "workspace 기준 하위 폴더, 기본값 ."}}, list_files),
    Tool("read_file", "workspace 안의 파일 내용을 읽는다.",
         {"path": {"type": "string"}}, read_file, required=("path",)),
    Tool("write_file", "workspace 안에 파일을 만들거나 전체 내용을 덮어쓴다.",
         {"path": {"type": "string"}, "content": {"type": "string"}}, write_file, required=("path", "content")),
    Tool("run_command", "workspace에서 명령을 실행한다. python, pytest, node, npm만 허용.",
         {"command": {"type": "string", "description": "예: pytest -q"}}, run_command,
         required=("command",), risky=True),
]

SYSTEM = """당신은 군 부대의 업무용 소프트웨어를 만드는 개발 에이전트입니다.
작업 순서: 요구사항 정리 → 파일 작성 → 테스트 작성 → run_command로 테스트 실행 → 실패하면 원인 수정 → 통과할 때까지 반복.
규칙:
- 외부 라이브러리 없이 Python 표준 라이브러리와 순수 HTML/CSS/JS로 만든다(망분리 환경 가정). 테스트는 pytest를 쓴다.
- 실제 부대명, 장비 제원, 개인정보를 넣지 않는다. 예시 데이터는 '가상'임을 표시한다.
- 끝나면 만든 파일, 실행 방법, 테스트 결과, 남은 한계를 한국어로 짧게 보고한다."""

DEFAULT_GOAL = (
    "정비 요청 관리 앱을 만들어라. "
    "1) maintenance.py: 요청 등록·상태 변경(접수→정비중→완료)·우선순위별 조회 기능과 JSON 파일 저장. "
    "2) test_maintenance.py: pytest 테스트. "
    "3) index.html: 같은 기능을 브라우저에서 쓰는 단일 파일 웹앱(localStorage 저장)."
)

if __name__ == "__main__":
    goal, auto_yes = parse_cli(DEFAULT_GOAL)
    print(run_agent(goal, TOOLS, SYSTEM, auto_yes=auto_yes))
    print(f"\n📁 결과물: {WORKSPACE}")
