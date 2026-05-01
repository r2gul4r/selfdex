# Selfdex

언어: [한국어](README.md) | [English](README.en.md)

Selfdex는 사용자가 고른 프로젝트를 Codex로 안전하게 작업하기 위한 감독형 지휘소다.

먼저 프로젝트를 읽고, 지금 가장 쓸모 있는 개선/발전/기능 작업 하나를 고른다. 그다음 승인받은 범위만 Codex에 넘기고, 리뷰와 검증을 통과한 뒤 필요하면 commit gate로 커밋/푸시/CI 확인까지 닫고 증거를 기록한다.

```text
프로젝트 선택 -> 방향 읽기 -> 다음 작업 선택 -> 승인 요청
-> 계약 고정 -> Codex 실행 -> 리뷰 -> 검증 -> commit gate -> 기록
```

Selfdex는 백그라운드 데몬도 아니고, 무작정 리팩터링하는 봇도 아니고, 저장소를 몰래 고치는 도구도 아니다. 사용자와 Codex 사이에서 작업을 작고, 유용하고, 추적 가능하게 묶어주는 제어층이다.

Selfdex는 구형 multi-agent kit이나 자체 topology 점수판이 아니다. 기본 실행 모델은 GPT-5.5 prompt guidance 방식의 command center이고, agent runtime은 공식 Codex native Subagents/MultiAgentV2다. `@selfdex` 호출은 필요한 경우 공식 subagents를 써도 된다는 명시 권한으로 취급한다.

## 설치

공개 설치 명령은 이거다:

```bash
npx selfdex install
```

이 명령은 Selfdex를 clone/update하고, home-local `@selfdex` Codex 플러그인을 설치한 뒤, `selfdex doctor`를 자동 실행한다. 즉 core Selfdex 세팅은 설치 명령 하나로 끝나야 한다.

단, GitHub 플러그인, ChatGPT Apps 플러그인, GPT Pro/GPT-5.5 권한 같은 계정 연결형 기능은 조용히 설치하거나 연결하지 않는다. `selfdex doctor`가 현재 상태를 보고 필요한 사용자 조치를 알려준다.

설치를 미리보기만 하려면:

```bash
npx selfdex install --dry-run
```

이 npm 명령은 `selfdex` 패키지가 npm에 publish된 뒤부터 바로 쓸 수 있다. publish 전에는 clone된 checkout에서 로컬 bootstrap을 실행한다:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

로컬 bootstrap 미리보기:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -DryRun
```

이미 checkout이 있고 `@selfdex` Codex 플러그인만 설치하려면:

```bash
python scripts/install_selfdex_plugin.py --root . --yes --format markdown
```

플러그인 설치 미리보기:

```bash
python scripts/install_selfdex_plugin.py --root . --dry-run --format markdown
```

설치 후 상태를 다시 확인하려면:

```bash
selfdex doctor
```

`selfdex doctor`가 확인하는 것:

- `@selfdex` 플러그인 설치 여부
- Codex marketplace 등록 여부
- Selfdex root 경로 연결 상태
- 필요한 로컬 스크립트 존재 여부
- GitHub Actions 확인용 fallback 존재 여부
- GitHub / ChatGPT Apps 플러그인 사용 가능 여부
- 공식 Codex subagent 설정 파일인 `.codex/config.toml`, `.codex/agents/*.toml` 상태
- Gmail 없이 CI 피드백을 받을 수 있는지

bootstrap 요구사항:

- `npx` 진입점을 위한 Node.js와 npm
- `install.ps1` 실행을 위한 PowerShell
- clone/update를 위한 Git
- 플러그인 설치 스크립트를 위한 Python 3
- 플러그인 discovery가 켜진 Codex

npm publish, npm credentials, registry ownership는 별도 승인과 계정 작업이 필요한 단계다. 이 저장소의 테스트나 bootstrap 검증은 publish를 수행하지 않는다.

## 사용

플러그인을 설치하거나 활성화한 뒤, 대상 프로젝트 Codex 세션에서 이렇게 호출한다:

```text
@selfdex read this project and choose the next safe task
```

별도 경로를 말하지 않으면 Selfdex는 현재 세션 디렉터리를 선택된 프로젝트로 본다.

`@selfdex` 호출은 다음 의미를 같이 가진다:

- Selfdex command-center 모드로 현재 프로젝트를 읽는다.
- 필요하면 공식 Codex native Subagents/MultiAgentV2를 사용해도 된다.
- main agent는 요구사항, 승인 경계, 통합, 기록을 맡는다.
- `explorer`, `docs_researcher`, `reviewer` 같은 read-only subagent는 탐색/문서/API/로그/리뷰를 맡을 수 있다.
- `worker` subagent는 계약이 고정되고 write boundary가 분리된 경우에만 파일을 수정한다.
- commit, push, publish, deploy, secrets, DB, production write, destructive 작업은 여전히 별도 승인이 필요하다.

첫 응답은 read-only 계획이어야 한다:

- 선택된 작업
- 왜 중요한지
- 제안 write boundary
- non-goals
- 검증 명령
- 위험도
- 승인 필요 여부
- Codex handoff prompt

사용자가 target-project write를 승인하면 Selfdex는 고정된 범위 안에서 실행 경로로 넘어갈 수 있다. 승인하지 않으면 루프는 계획에서 멈춘다.

## 하는 일

Selfdex는 방향, 조율, 구현을 분리한다:

- GPT / Pro extended mode는 사용자가 요청하거나 승인한 경우에만 product, milestone, roadmap, priority, 개선 방향, 추가 기능 같은 고수준 방향 판단에 쓴다. `@chatgpt-apps`가 사용 가능한 세션에서는 이 방향 리뷰 경로로 취급한다.
- Selfdex는 읽고, 순위를 매기고, 계약을 고정하고, 승인을 받고, 기록하고, uncontrolled autonomy를 막는다.
- Codex는 승인된 계약 안에서 구현, 검증, 디버깅, diff review, repair를 한다. 코드 리뷰는 Codex native `reviewer` subagent가 맡는다.

Selfdex가 찾는 다음 작업 유형:

- `repair`: 깨진 동작 복구
- `hardening`: 기존 동작을 덜 깨지게 강화
- `improvement`: 유지보수성이나 명확성 개선
- `capability`: 빠진 시스템 능력 추가
- `automation`: 반복 조율 작업 자동화
- `direction`: 제품/기술 방향을 더 나은 곳으로 이동

좋은 후보는 단순히 “문제가 있다”가 아니다. 기준은 이거다:

```text
이 프로젝트는 이 방향으로 움직이면 더 좋아지고,
그 첫 단계로 지금 할 수 있는 가장 작은 안전한 작업이 이것이다.
```

## 실행 모델

Selfdex는 공식 Codex native Subagents/MultiAgentV2 기준을 쓴다:

- `main agent`: 요구사항, 작업 선택, 승인 경계, 통합, 최종 보고, run record
- `explorer`: `gpt-5.5` low, read-only 코드베이스 탐색과 근거 수집
- `docs_researcher`: `gpt-5.5` medium, read-only 공식 문서/API 동작 확인
- `worker`: `gpt-5.5` high, 고정된 write boundary 하나 안에서 구현
- `reviewer`: `gpt-5.5` xhigh, read-only correctness, regression, security, missing tests 리뷰

`explorer`와 `worker`는 Codex built-in agent 이름과 맞춘다. `reviewer`와
`docs_researcher`는 Codex의 custom agent 패턴에 맞춘 프로젝트 scoped 역할이다.
이름을 예쁘게 바꾸는 것보다 Codex가 실제로 인식하는 agent name을 안정적으로
유지하는 쪽을 우선한다.

작고 결합된 작업은 main agent가 바로 처리한다. 탐색, 문서 확인, 로그 분석, 리뷰, 분리된 구현 slice가 독립적으로 움직일 수 있으면 공식 subagents를 쓴다. 예전 로컬 제어 로직은 active runtime이 아니다.

GPT-5.5 prompt guidance는 운영 원칙이지 자동 GPT 호출이 아니다. 제품 방향, milestone, roadmap, priority, 개선사항, 추가 기능 review는 사용자가 GPT / Pro extended mode를 요청하거나 명시적으로 승인해야 한다. `@chatgpt-apps`는 이 제품/앱 방향 리뷰에 쓰고, 일반 코드 diff review는 Codex native `reviewer` subagent로 처리한다.

## 안전 모델

Selfdex는 외부 프로젝트를 항상 read-only로 시작한다.

대상 프로젝트 write는 현재 thread에서 명시 승인받아야 한다. 폴더 단위 승인이 있어도 hard approval zone은 우회하지 않는다.

항상 hard approval이 필요한 것:

- 파괴적 filesystem 또는 Git history 작업
- secrets, credentials, private keys, token 접근
- paid API calls
- public deploy
- database migration 또는 production write
- 승인 경계 밖 cross-workspace 변경
- global Codex config, installer, plugin, MCP setup 변경

ChatGPT Apps와 MCP surface는 read-only가 먼저다. 첫 app surface는 등록 프로젝트, 다음 추천 작업, 최근 실행 기록, 승인 상태만 보여줄 수 있다. 명시 승인 전에는 target-project write 실행을 노출하면 안 된다.

## 현재 기능

설치 및 테스트된 표면:

- `package.json`과 `bin/selfdex.js`는 npm-style `selfdex` CLI를 정의한다.
- `install.ps1`은 Selfdex를 bootstrap하고 home-local 플러그인을 설치한다.
- `plugins/selfdex/`는 `@selfdex` 호출에 쓰는 Codex 플러그인을 담고 있다.
- `.codex/config.toml`과 `.codex/agents/*.toml`은 공식 Codex native Subagents/MultiAgentV2 역할, `gpt-5.5` 모델, 역할별 reasoning effort를 정의한다.
- `.agents/plugins/marketplace.json`은 repo-local 플러그인 패키지를 알린다.
- `scripts/install_selfdex_plugin.py`는 선택한 home에 플러그인을 설치한다.
- `scripts/check_selfdex_setup.py`는 설치 후 core setup, local fallback, 권장 Codex integration 상태를 확인한다.
- `scripts/check_commit_gate.py`는 리뷰/검증이 끝난 작업을 커밋해도 되는지 확인한다.
- `scripts/plan_external_project.py`는 target project를 읽고 target을 수정하지 않은 채 frozen task contract를 만든다.
- `scripts/run_target_codex.py`는 승인된 target-project 실행 경로를 branch와 run-record metadata와 함께 실행할 수 있다.
- `scripts/build_control_surface_snapshot.py`는 read-only control surface payload를 만든다.
- `scripts/control_surface_mcp_server.py`는 dependency-free local `/mcp` JSON-RPC scaffold로 read-only payload를 노출한다.
- `scripts/check_selfdex_plugin.py`, `scripts/check_campaign_budget.py`, `scripts/check_doc_drift.py`는 plugin wiring, contract boundary, README drift를 검증한다.
- `scripts/*.py`에는 나머지 scanner, planner, recorder, extractor, checker가 들어 있다.

의도적으로 막아둔 것:

- background polling loop 없음
- multi-candidate 자동 실행 없음
- 승인 없는 target-project write 없음
- 자동 GPT direction review 없음
- legacy `codex_multiagent` baseline 없음
- 구형 Selfdex topology 점수판을 active runtime으로 사용하지 않음
- npm publish step 없음
- read-only validation이 implementation evidence를 대체한다는 주장 없음
- review/verification 없이 자동 commit/push 없음

## Quick Start

이 저장소를 점검한다:

```bash
python scripts/build_project_direction.py --root . --format markdown
python scripts/plan_next_task.py --root . --format markdown
```

등록된 외부 프로젝트를 read-only로 점검한다:

```bash
python scripts/check_external_validation_readiness.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --format markdown
python scripts/build_external_candidate_snapshot.py --root . --project-id daboyeo --format markdown
```

대상 프로젝트를 수정하지 않고 작업 계약을 만든다:

```bash
python scripts/plan_external_project.py --root . --project-root ../daboyeo --project-name daboyeo --format markdown
```

target-project orchestrator를 dry-run으로 실행한다:

```bash
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --format markdown
```

명시 승인 후에만 target 실행을 켠다:

```bash
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --execute --format markdown
```

read-only control surface를 만든다:

```bash
python scripts/build_control_surface_snapshot.py --root . --format markdown
python scripts/control_surface_mcp_server.py --root . --describe-tools
```

유지보수 체크:

```bash
python scripts/check_campaign_budget.py --root . --format markdown
python scripts/check_doc_drift.py --root . --format markdown
python scripts/collect_repo_metrics.py --root . --pretty
python scripts/extract_test_gap_candidates.py --root . --format markdown
```

## 기록

Selfdex는 작업 기록을 `runs/` 아래에 모은다.

대상 프로젝트 기록 경로:

```text
runs/<project_key>/<YYYYMMDD-HHMMSS>-<task-slug>.md
```

non-trivial run에는 최소한 이 내용이 있어야 한다:

- project id와 project root
- selected candidate
- frozen contract
- approval status
- changed files
- verification commands and results
- repair attempts
- final status: `completed`, `failed`, `blocked`, `stopped`
- next candidate 또는 stop reason

## 저장소 지도

핵심 control files:

- `README.en.md`는 영어 README mirror다.
- `AGENTS.md`는 저장소 실행 규칙을 정의한다.
- `AUTOPILOT.md`는 supervised loop policy를 정의한다.
- `CAMPAIGN_STATE.json`은 machine-readable campaign contract다.
- `CAMPAIGN_STATE.md`는 campaign intent의 human-readable mirror다.
- `STATE.json`은 machine-readable active task contract다.
- `STATE.md`는 active task와 write boundary의 human-readable mirror다.
- `project_registry.json`은 tool-readable project registry다.
- `PROJECT_REGISTRY.md`는 registry와 read-only boundary를 미러링한다.
- `docs/SELFDEX_FINAL_GOAL.md`은 north-star contract다.
- `docs/CANDIDATE_QUALITY_RUBRIC.md`는 candidate usefulness scoring을 정의한다.
- `docs/SELFDEX_HANDOFF.md`는 cross-machine continuity note다.
- `docs/ORCHESTRATION_DECISION_PLAN.md`는 orchestration decision을 설명한다.
- `runs/`는 run evidence를 저장한다.
- `examples/quality_signal_samples.json`, `examples/external_validation_planner_sample.json`, `examples/candidate_quality_sample.json`은 validation fixture다.

Active external validation target은 `PROJECT_REGISTRY.md`에 있다. 과거 `codex_multiagent` report는 `runs/external-validation/` 아래 legacy/reference evidence로 남아 있지만, 더 이상 Selfdex의 active baseline이나 registry proof target이 아니다.

Installer와 plugin files:

- `package.json`은 npm package metadata와 executable을 정의한다.
- `bin/selfdex.js`는 `install.ps1`과 setup doctor를 감싸는 npm CLI wrapper다.
- `install.ps1`은 Selfdex를 clone/update하고 plugin installer를 실행한 뒤, 명시적으로 skip하지 않으면 setup doctor를 실행한다.
- `plugins/selfdex/`는 repo-local Codex plugin package다.
- `.agents/plugins/marketplace.json`은 Codex용 plugin을 알린다.

## 검증

문서와 계약 변경에는 좁은 체크를 쓴다:

```bash
python scripts/check_doc_drift.py --root . --format json
python scripts/check_campaign_budget.py --root . --include-git-diff --format json
git diff --check
```

코드, installer, plugin, workflow 변경 후에는 전체 체크를 쓴다:

```bash
node bin/selfdex.js --help
node bin/selfdex.js install --dry-run --install-root C:/tmp/selfdex-npx-dry-run
node bin/selfdex.js doctor --help
npm pack --dry-run
python -m compileall -q scripts tests
python -m unittest discover -s tests
python scripts/check_coverage_signal.py --input examples/quality_signal_samples.json --format json
python scripts/build_project_direction.py --root . --format json
python scripts/build_external_candidate_snapshot.py --root . --format json
python scripts/build_external_validation_package.py --root . --format json
python scripts/plan_external_project.py --root . --project-id daboyeo --format json
python scripts/run_target_codex.py --root . --project-root ../daboyeo --project-name daboyeo --format json
```

승인된 commit/push 뒤에는 GitHub를 CI feedback source로 쓴다:

```bash
python scripts/check_commit_gate.py --root . --commit-message "docs: verify commit gate" --format json
python scripts/check_github_actions_status.py --root . --format json
```

CI는 `.github/workflows/check.yml`에서 baseline을 실행한다:

```bash
make check
```

## 현재 방향

Selfdex는 현재 supervised local command center foundation으로 준비되어 있다:

- project-session invocation은 `@selfdex`로 가능하다.
- npm publish 뒤 설치 경로는 `npx selfdex install`이다.
- 선택된 외부 프로젝트에 대한 read-only planning이 있다.
- target execution은 approval-gated 상태다.
- commit gate는 review와 verification 뒤에만 선택적으로 실행된다.
- run evidence와 state contract가 기록된다.
- verification이 현재 safety model을 보호한다.

다음 제품 단계는 더 큰 autonomy가 아니다. read-only planning, explicit approval, local verification, 공식 Codex native Subagents/MultiAgentV2, run records를 유지하면서 approved project-session flow를 더 매끄럽게 만드는 것이다.
