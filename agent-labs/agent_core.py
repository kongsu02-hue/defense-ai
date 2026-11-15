"""AI 에이전트 공통 엔진

세 실습(앱 개발, GitHub, PC 제어)이 함께 쓰는 에이전트 루프입니다.

  목표 → Claude가 도구 선택 → (위험 도구면 사람 승인) → 실행 → 결과 관찰 → 반복

운용 원칙을 코드로 구현합니다.
  - 최소 권한: 실습마다 필요한 도구만 넘긴다.
  - 사람 승인: risky=True 도구는 실행 전에 y/N 확인을 받는다.
  - 기록·감사: 모든 도구 호출과 결과를 logs/*.jsonl 에 남긴다.
  - 폭주 방지: 최대 턴 수를 넘으면 멈춘다.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

import anthropic

MODEL = "claude-opus-5-5"
LOG_DIR = Path(__file__).parent / "logs"

# Windows 콘솔에서 한글·이모지가 깨지지 않도록
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class Tool:
    name: str
    description: str
    params: dict          # {"이름": {"type": ..., "description": ...}}
    func: Callable[..., object]
    required: tuple = ()
    risky: bool = False   # True면 실행 전에 사람 승인

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description + (" (실행 전 사용자 승인 필요)" if self.risky else ""),
            "input_schema": {
                "type": "object",
                "properties": self.params,
                "required": list(self.required),
            },
        }


def _log(record: dict) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    path = LOG_DIR / f"agent-{datetime.now():%Y%m%d}.jsonl"
    record = {"time": datetime.now().isoformat(timespec="seconds"), **record}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _approve(tool: Tool, args: dict, auto_yes: bool) -> bool:
    if not tool.risky:
        return True
    print(f"\n🛑 승인 요청: {tool.name}")
    for k, v in args.items():
        text = str(v)
        print(f"   {k}: {text[:400]}{' …' if len(text) > 400 else ''}")
    if auto_yes:
        print("   (--yes 옵션으로 자동 승인)")
        return True
    return input("   실행할까요? (y/N) ").strip().lower() == "y"


def _execute(tool: Tool, args: dict, auto_yes: bool) -> tuple[str, bool]:
    if not _approve(tool, args, auto_yes):
        return "사용자가 이 작업을 거부했습니다. 다른 방법을 제안하거나 작업을 멈추세요.", True
    try:
        result = tool.func(**args)
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=1)
        return text[:20000], False
    except Exception as e:  # 도구 오류도 에이전트에게 알려 스스로 고치게 한다
        return f"오류: {type(e).__name__}: {e}", True


def run_agent(goal: str, tools: list[Tool], system: str, max_turns: int = 25, auto_yes: bool = False) -> str:
    """목표를 달성할 때까지 에이전트 루프를 돈다. 최종 답변 텍스트를 반환한다."""
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print("ℹ️  ANTHROPIC_API_KEY가 없습니다. `ant auth login` 프로필이 없다면 키를 설정하세요.")

    client = anthropic.Anthropic()
    by_name = {t.name: t for t in tools}
    messages: list = [{"role": "user", "content": goal}]
    _log({"event": "start", "goal": goal, "tools": list(by_name)})
    print(f"🎯 목표: {goal}\n")

    for turn in range(1, max_turns + 1):
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=system,
            tools=[t.schema() for t in tools],
            messages=messages,
            output_config={"effort": "high"},
            # 안전 분류기가 거절하면 서버가 자동으로 다른 모델로 재시도
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

        if response.stop_reason == "refusal":
            print("⛔ 요청이 거절되었습니다.")
            _log({"event": "refusal", "turn": turn})
            return ""

        # 사고(thinking) 블록까지 그대로 다시 넣어야 다음 턴이 이어진다
        messages.append({"role": "assistant", "content": response.content})
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"💬 {block.text.strip()}\n")

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            if response.stop_reason == "max_tokens":
                messages.append({"role": "user", "content": "출력이 잘렸습니다. 이어서 진행하세요."})
                continue
            final = "".join(b.text for b in response.content if b.type == "text")
            _log({"event": "done", "turn": turn})
            return final

        results = []
        for call in tool_uses:
            tool = by_name.get(call.name)
            print(f"🔧 [{turn}] {call.name}({json.dumps(call.input, ensure_ascii=False)[:200]})")
            if tool is None:
                text, is_error = f"알 수 없는 도구: {call.name}", True
            else:
                text, is_error = _execute(tool, dict(call.input), auto_yes)
            print(f"   {'❌' if is_error else '👀'} {text[:300].replace(chr(10), ' ⏎ ')}\n")
            _log({"event": "tool", "turn": turn, "tool": call.name, "input": call.input,
                  "error": is_error, "result": text[:2000]})
            results.append({"type": "tool_result", "tool_use_id": call.id, "content": text, "is_error": is_error})
        # 여러 도구 결과는 한 메시지에 모아 보낸다
        messages.append({"role": "user", "content": results})

    print("⚠️ 최대 턴 수에 도달해 멈췄습니다.")
    _log({"event": "max_turns"})
    return ""


def parse_cli(default_goal: str) -> tuple[str, bool]:
    args = [a for a in sys.argv[1:] if a != "--yes"]
    return (" ".join(args) or default_goal), ("--yes" in sys.argv)
