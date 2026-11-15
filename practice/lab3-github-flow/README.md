# 실습 3. GitHub로 협업하고 배포하기 — 이슈 → 브랜치 → PR → 자동 테스트 → 배포

**목표:** 실습 1·2에서 만든 앱을 팀 저장소에 올리고, 사람이 검토하고 자동 테스트를 통과한 변경만 반영되게 한다.
**도구:** Git, GitHub CLI(`gh`), `agent-labs/lab2_github_agent.py` · **시간:** 90분

## 0. 준비 (1회)

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
gh auth login --web                 # 브라우저에서 코드 입력 후 승인
gh auth refresh -s workflow         # Actions 워크플로 파일을 푸시하려면 필요한 권한
```

> 처음 로그인하면 토큰 권한이 `repo, gist, read:org`뿐이라 `.github/workflows/` 파일을 푸시할 때 거부됩니다.
> 실제로 자주 만나는 오류이므로 직접 겪고 해결해 봅니다.

## 1. 저장소 만들기

```powershell
cd C:\work\checklist                # 실습 1 결과물 폴더
git init -b main
git add . ; git commit -m "장비 점검 체크리스트 초기 버전 (AI 에이전트 작성, 사람 검증)"
gh repo create checklist --private --source . --push
```

## 2. 이슈 → 브랜치 → PR

```powershell
gh issue create --title "이상 항목 사진 첨부" --body "점검 시 이상 부위 사진 첨부 기능"
git switch -c feature/photo
# … Claude Code로 기능 구현 …
git add . ; git commit -m "이상 항목 사진 첨부 (#1)"
git push -u origin feature/photo
gh pr create --draft --title "이상 항목 사진 첨부" --body "Closes #1`n테스트: 휴대폰에서 촬영 후 저장 확인"
```

같은 일을 에이전트에게 맡겨 본다 (쓰기 작업마다 승인 요청이 뜸):

```powershell
python agent-labs\lab2_github_agent.py --repo C:\work\checklist "열린 이슈를 확인하고 #1을 처리할 브랜치와 초안 PR을 만들어라"
```

## 3. 자동 테스트 (GitHub Actions)

이 폴더의 [`ci.yml`](ci.yml)을 저장소의 `.github/workflows/ci.yml`로 복사하고 푸시한다.
PR을 열 때마다 pytest가 자동 실행되고, 실패하면 PR 화면에 빨간 X가 표시된다.

```powershell
gh run list            # 실행 결과
gh run view --log-failed
```

## 4. 배포 (GitHub Pages)

```powershell
gh api -X POST repos/{owner}/checklist/pages -f "source[branch]=main" -f "source[path]=/"
```

> 무료 계정에서 Pages는 **공개 저장소**만 가능합니다. 공개 전에 실제 부대명·개인정보·내부 자료가 없는지 반드시 확인합니다.

## 5. 브랜치 보호

저장소 Settings → Branches에서 `main`에 "PR 필수, 테스트 통과 필수"를 켠다.
이제 사람도 에이전트도 검토와 테스트 없이 `main`을 바꿀 수 없다.

## 점검표

- [ ] 이슈 번호가 커밋·PR에 연결되어 있다
- [ ] 커밋 메시지에 AI 작성 여부가 표시되어 있다
- [ ] PR에서 Actions 테스트가 통과했다
- [ ] 다른 교육생이 PR을 검토하고 승인했다
- [ ] 저장소에 비밀번호·토큰·실제 정보가 없다 (`git log -p | Select-String "password|token|sk-"`)
