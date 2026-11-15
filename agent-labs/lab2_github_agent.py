"""에이전트 실습 2. GitHub 에이전트

로컬 저장소와 GitHub를 다루는 에이전트입니다. 상태 확인·이슈 정리·브랜치·커밋·PR·Actions 확인을 맡깁니다.
읽기 도구는 바로 실행하고, 저장소를 바꾸는 도구(이슈 생성, 커밋, 푸시, PR)는 매번 사람 승인을 받습니다.

준비
  - Git, GitHub CLI 설치 후 `gh auth login`
  - 실습용 저장소를 하나 clone 해 둔다 (예: 본 과정 저장소를 fork)

실행
  python lab2_github_agent.py --repo C:\\work\\my-repo
  python lab2_github_agent.py --repo C:\\work\\my-repo "열린 이슈를 우선순위로 정리하고, 가장 쉬운 것 하나를 고칠 브랜치와 PR 초안을 만들어라"
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from agent_core import Tool, parse_cli, run_agent


def _find(exe: str, fallbacks: list[str]) -> str:
    found = shutil.which(exe)
    if found:
        return found
    for f in fallbacks:
        if Path(f).exists():
            return f
    raise FileNotFoundError(f"{exe}를 찾을 수 없습니다. 설치 후 PATH에 추가하세요.")


GIT = _find("git", [r"C:\Program Files\Git\cmd\git.exe"])
GH = _find("gh", [r"C:\Program Files\GitHub CLI\gh.exe"])
# gh는 내부에서 git을 PATH로 찾으므로, git 폴더를 PATH에 넣어 준다
ENV = {**os.environ, "PATH": str(Path(GIT).parent) + os.pathsep + os.environ.get("PATH", "")}

# --repo 인자 처리 (agent_core.parse_cli 전에 제거)
REPO = Path.cwd()
if "--repo" in sys.argv:
    i = sys.argv.index("--repo")
    REPO = Path(sys.argv[i + 1]).resolve()
    del sys.argv[i:i + 2]


def _run(argv: list[str]) -> str:
    done = subprocess.run(argv, cwd=REPO, env=ENV, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    out = (done.stdout + ("\n" + done.stderr if done.stderr.strip() else "")).strip()
    if done.returncode != 0:
        raise RuntimeError(out or f"exit={done.returncode}")
    return out or "(출력 없음, 성공)"


# ---- 읽기 도구 ----
def repo_status() -> str:
    return _run([GIT, "status", "-sb"]) + "\n\n최근 커밋:\n" + _run([GIT, "log", "--oneline", "-n", "10"])


def show_diff(staged: bool = False) -> str:
    return _run([GIT, "diff", "--stat", "--patch", *(["--staged"] if staged else [])])[:15000]


def read_file(path: str) -> str:
    p = (REPO / path).resolve()
    if REPO not in p.parents:
        raise PermissionError("저장소 밖 파일은 읽을 수 없습니다.")
    return p.read_text(encoding="utf-8", errors="replace")[:15000]


def list_issues(state: str = "open") -> str:
    return _run([GH, "issue", "list", "--state", state, "--limit", "30",
                 "--json", "number,title,labels,createdAt", "--template",
                 "{{range .}}#{{.number}} {{.title}} [{{range .labels}}{{.name}} {{end}}]\n{{end}}"])


def view_issue(number: int) -> str:
    return _run([GH, "issue", "view", str(number), "--comments"])


def list_prs() -> str:
    return _run([GH, "pr", "list", "--limit", "20"])


def list_workflow_runs() -> str:
    return _run([GH, "run", "list", "--limit", "10"])


# ---- 쓰기 도구 (승인 필요) ----
def create_issue(title: str, body: str, labels: str = "") -> str:
    argv = [GH, "issue", "create", "--title", title, "--body", body]
    if labels:
        argv += ["--label", labels]
    return _run(argv)


def comment_issue(number: int, body: str) -> str:
    return _run([GH, "issue", "comment", str(number), "--body", body])


def create_branch(name: str) -> str:
    return _run([GIT, "switch", "-c", name])


def write_file(path: str, content: str) -> str:
    p = (REPO / path).resolve()
    if REPO not in p.parents:
        raise PermissionError("저장소 밖에는 쓸 수 없습니다.")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"{path} 저장"


def commit(message: str, paths: list[str]) -> str:
    _run([GIT, "add", "--", *paths])
    return _run([GIT, "commit", "-m", message])


def push(branch: str) -> str:
    return _run([GIT, "push", "-u", "origin", branch])


def create_pr(title: str, body: str, draft: bool = True) -> str:
    return _run([GH, "pr", "create", "--title", title, "--body", body, *(["--draft"] if draft else [])])


S = {"type": "string"}
TOOLS = [
    Tool("repo_status", "브랜치, 변경 파일, 최근 커밋 10개를 본다.", {}, repo_status),
    Tool("show_diff", "작업 중인 변경 내용(diff)을 본다.", {"staged": {"type": "boolean"}}, show_diff),
    Tool("read_file", "저장소 안 파일을 읽는다.", {"path": S}, read_file, required=("path",)),
    Tool("list_issues", "GitHub 이슈 목록을 본다.", {"state": {"type": "string", "enum": ["open", "closed", "all"]}}, list_issues),
    Tool("view_issue", "이슈 본문과 댓글을 본다.", {"number": {"type": "integer"}}, view_issue, required=("number",)),
    Tool("list_prs", "열린 Pull Request 목록을 본다.", {}, list_prs),
    Tool("list_workflow_runs", "GitHub Actions 최근 실행 결과를 본다.", {}, list_workflow_runs),
    Tool("create_issue", "새 이슈를 만든다.", {"title": S, "body": S, "labels": {"type": "string", "description": "쉼표로 구분, 이미 있는 라벨만"}},
         create_issue, required=("title", "body"), risky=True),
    Tool("comment_issue", "이슈에 댓글을 단다.", {"number": {"type": "integer"}, "body": S},
         comment_issue, required=("number", "body"), risky=True),
    Tool("create_branch", "새 브랜치를 만들고 전환한다.", {"name": S}, create_branch, required=("name",), risky=True),
    Tool("write_file", "저장소 안 파일을 만들거나 덮어쓴다.", {"path": S, "content": S},
         write_file, required=("path", "content"), risky=True),
    Tool("commit", "지정한 파일만 스테이징해 커밋한다.", {"message": S, "paths": {"type": "array", "items": S}},
         commit, required=("message", "paths"), risky=True),
    Tool("push", "브랜치를 origin에 푸시한다. main 직접 푸시는 피한다.", {"branch": S}, push, required=("branch",), risky=True),
    Tool("create_pr", "현재 브랜치로 Pull Request를 만든다. 기본은 초안(draft).", {"title": S, "body": S, "draft": {"type": "boolean"}},
         create_pr, required=("title", "body"), risky=True),
]

SYSTEM = f"""당신은 군 소프트웨어 개발팀의 GitHub 운영 보조 에이전트입니다. 작업 저장소: {REPO}
원칙:
- 먼저 읽기 도구로 상황을 파악하고, 무엇을 왜 바꿀지 설명한 다음 쓰기 도구를 쓴다.
- main 브랜치에 직접 커밋·푸시하지 않는다. 작업은 브랜치 → 커밋 → 초안 PR 순서로 한다.
- 커밋 메시지와 PR 본문에 변경 이유, 테스트 방법, 'AI 에이전트가 작성' 표시를 남긴다(추적성).
- 비밀번호, 토큰, 실제 부대·작전 정보가 커밋에 들어가지 않는지 diff로 확인한다.
- 마지막에 한 일과 사람이 확인해야 할 것을 한국어로 요약한다."""

DEFAULT_GOAL = "저장소 상태와 열린 이슈, 최근 Actions 결과를 점검하고 오늘 처리할 일 3가지를 우선순위로 정리하라."

if __name__ == "__main__":
    goal, auto_yes = parse_cli(DEFAULT_GOAL)
    print(f"📂 저장소: {REPO}")
    print(run_agent(goal, TOOLS, SYSTEM, auto_yes=auto_yes))
