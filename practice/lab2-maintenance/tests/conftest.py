"""SOLUTION=1 이면 참고 답안(solution/)을, 아니면 실습 파일(maintenance.py)을 테스트한다."""
import os
import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root / "solution" if os.environ.get("SOLUTION") == "1" else root))
