# Git Secret 제거 완전 가이드 - 실제 작업 기록

이 문서는 2025-06-08에 실제로 수행한 Git 히스토리에서 secret을 제거하는 전체 과정을 기록합니다.

## 목차
1. [문제 상황](#문제-상황)
2. [초기 진단](#초기-진단)
3. [백업 생성](#백업-생성)
4. [첫 번째 시도: Interactive Rebase](#첫-번째-시도-interactive-rebase)
5. [두 번째 시도: Filter-branch](#두-번째-시도-filter-branch)
6. [추가 문제 발견](#추가-문제-발견)
7. [코드 수정](#코드-수정)
8. [BFG를 사용한 최종 해결](#bfg를-사용한-최종-해결)
9. [마무리 작업](#마무리-작업)

---

## 문제 상황

### 초기 push 시도
```bash
git push origin main
```
**결과**: GitHub push protection 에러
```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - GITHUB PUSH PROTECTION
remote: - Push cannot contain secrets
```

**원인**: 
- 커밋 `ca0eef3`와 `562f4e4`에 `.env.test` 파일 포함
- 여러 소스 파일에 Discord Bot Token 하드코딩

---

## 초기 진단

### 현재 상태 확인
```bash
git status
# 출력: On branch main
# Your branch is ahead of 'origin/main' by 16 commits.
```
**의미**: 로컬에 16개의 push되지 않은 커밋이 있음

### 커밋 히스토리 확인
```bash
git log --oneline -10
# 출력:
# 85d9efa fix: barrack 명령어 버그 수정 (#1)
# 9b3ef33 WIP: OCR 기능 구현 진행 중
# ac7745b feat: Group8 지원 및 테스트 시스템 전면 개선
# ... (이하 생략)
```
**의미**: 최근 커밋들 확인, 어떤 작업들이 있었는지 파악

### push되지 않은 커밋 개수 확인
```bash
git rev-list --count origin/main..HEAD
# 출력: 16
```
**의미**: 정확히 16개의 커밋이 origin보다 앞서있음을 확인

---

## 백업 생성

### 전체 프로젝트 백업
```bash
tar -czf ../PTCGPBKor_backup_$(date +%Y%m%d_%H%M%S).tar.gz .
ls -lh ../PTCGPBKor_backup*.tar.gz | tail -1
# 출력: -rw-r--r--@ 1 papawolf staff 92M 6 8 01:06 ../PTCGPBKor_backup_20250608_010645.tar.gz
```
**설명**:
- `tar`: 파일을 하나로 묶는 명령어
- `-c`: create (생성)
- `-z`: gzip으로 압축
- `-f`: 파일로 저장
- `$(date +%Y%m%d_%H%M%S)`: 현재 시간을 파일명에 포함 (20250608_010645 형식)
- **중요**: 히스토리 수정은 위험하므로 반드시 백업 먼저!

---

## 첫 번째 시도: Interactive Rebase

### 문제가 있는 커밋 확인
```bash
git show ca0eef3 --name-only | grep -A5 -B5 ".env.test"
# 출력: .env.test 파일이 이 커밋에 추가됨

git show 562f4e4 --name-only | grep -A5 -B5 ".env.test"
# 출력: .env.test 파일이 이 커밋에서도 수정됨
```
**설명**:
- `git show`: 특정 커밋의 내용 표시
- `--name-only`: 파일 이름만 표시
- `grep -A5 -B5`: 찾은 줄의 위(Before) 5줄, 아래(After) 5줄 표시

### Interactive rebase 시도
```bash
git rebase -i ca0eef3~1
# 결과: Successfully rebased and updated refs/heads/main.
```
**문제**: vim 에디터가 열리지 않고 자동으로 완료됨

### 다른 방법 시도
```bash
# rebase 할 커밋 목록만 보기
GIT_SEQUENCE_EDITOR="cat" git rebase -i ca0eef3~1
# 출력: 16개의 커밋 목록 표시
```
**설명**: 
- `GIT_SEQUENCE_EDITOR="cat"`: 에디터 대신 cat 명령어로 내용만 출력
- 실제로 수정하지는 않고 어떤 커밋들이 있는지만 확인

### vim 설정 시도
```bash
git config --global core.editor "vim"
```
**의미**: Git의 기본 에디터를 vim으로 설정

### Rebase 포기
```bash
git rebase --abort
```
**이유**: Interactive rebase는 너무 복잡하고 충돌 가능성이 높음

---

## 두 번째 시도: Filter-branch

### filter-branch로 .env.test 제거
```bash
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env.test' \
  --prune-empty --tag-name-filter cat -- --all
```
**출력**:
```
WARNING: git-filter-branch has a glut of gotchas...
Rewrite ca0eef3... rm '.env.test'
Rewrite 562f4e4... rm '.env.test'
...
```

**옵션 설명**:
- `--force`: 이전 백업 무시하고 강제 실행
- `--index-filter`: 각 커밋의 인덱스(staging area)를 수정
- `git rm --cached --ignore-unmatch .env.test`: 
  - `--cached`: 파일 시스템이 아닌 Git 인덱스에서만 제거
  - `--ignore-unmatch`: 파일이 없어도 에러 발생하지 않음
- `--prune-empty`: 빈 커밋 제거
- `--tag-name-filter cat`: 태그 이름 유지
- `-- --all`: 모든 브랜치에 적용

### filter-branch 정리
```bash
# filter-branch가 만든 백업 참조 제거
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d

# Git 가비지 컬렉션
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```
**설명**:
- `refs/original/`: filter-branch가 원본 보존을 위해 만든 백업
- `reflog expire`: 참조 로그 만료
- `gc --prune=now --aggressive`: 즉시 가비지 컬렉션 수행

### 확인
```bash
git log --oneline --name-only | grep -B2 ".env.test" | head -20
# 출력: (아무것도 없음 - 성공적으로 제거됨)
```

---

## 추가 문제 발견

### Push 재시도
```bash
git push origin main
```
**새로운 에러**:
```
remote: - Discord Bot Token
remote: locations:
remote:   - commit: b7c4a0efb16d6dccc403f8576d17e7203d7d57ad
remote:     path: src/bots/Poke3.py:15
remote:     path: src/bots/Poke4.py:12
remote:     path: src/utils/deleteOldPost.py:10
```
**문제**: 다른 파일들에 Discord 토큰이 하드코딩되어 있음!

---

## 코드 수정

### 문제 파일 확인 및 수정

#### Poke3.py 수정
```python
# 기존 (line 15)
DISCORD_TOKEN = "MTM1NjU1MjI4NDc1Mzg5MTM3OQ.XXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# 수정 후
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')  # 환경변수에서 읽어옴
```

#### Poke4.py 수정
```python
# os import 추가
import os

# 토큰 부분 수정 (line 12)
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')  # 환경변수에서 읽어옴
```

#### deleteOldPost.py 수정
```python
# os import 추가
import os

# 토큰 부분 수정 (line 10)
DISCORD_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')  # 환경변수에서 읽어옴
```

### 변경사항 커밋
```bash
git add -u
git status
# 출력: 3개 파일 수정됨 확인

git commit -m "fix: Discord 토큰을 환경변수로 변경

- Poke3.py, Poke4.py, deleteOldPost.py에서 하드코딩된 토큰 제거
- DISCORD_BOT_TOKEN 환경변수 사용하도록 변경
- 보안 취약점 해결"
```

---

## BFG를 사용한 최종 해결

### BFG 설치
```bash
brew install bfg
```
**출력**: Java 의존성 설치 후 BFG 설치 완료
**BFG란?**: Big Friendly Giant - filter-branch보다 100배 빠른 히스토리 정리 도구

### 제거할 토큰 파일 생성
```bash
echo "MTM1NjU1MjI4NDc1Mzg5MTM3OQ.XXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXXXX" > passwords.txt
```
**설명**: BFG가 찾아서 제거할 문자열 목록

### Mirror 클론 생성
```bash
git clone --mirror . ../PTCGPBKor.git
# 출력: Cloning into bare repository '../PTCGPBKor.git'... done.
```
**설명**:
- `--mirror`: 모든 참조(branches, tags)를 포함한 완전한 복사본
- BFG는 안전을 위해 원본이 아닌 mirror에서만 작동

### BFG 실행
```bash
bfg --replace-text passwords.txt ../PTCGPBKor.git
```
**출력 요약**:
```
Protected commits: 1 (최신 커밋은 보호됨)
Found 42 commits
Changed files:
  Poke3.py | f58a1967 ⇒ da40c2d0
  Poke4.py | 8a0b8c28 ⇒ 9ba5a88a
  deleteOldPost.py | 869ec5e4 ⇒ 5a8b58d0
```
**의미**: 3개 파일에서 토큰이 제거되고 파일 해시가 변경됨

### BFG 작업 후 정리
```bash
git -C ../PTCGPBKor.git reflog expire --expire=now --all
git -C ../PTCGPBKor.git gc --prune=now --aggressive
```
**설명**: 
- `-C`: 다른 디렉토리에서 git 명령 실행
- BFG가 남긴 임시 데이터 정리

### 정리된 히스토리 가져오기
```bash
# BFG 결과를 remote로 추가
git remote add bfg ../PTCGPBKor.git

# 정리된 main 브랜치 가져오기
git fetch bfg main:main-cleaned
# 출력: * [new branch] main -> main-cleaned

# 정리된 브랜치로 전환
git checkout main-cleaned
```

### 브랜치 이름 정리
```bash
# 기존 main을 main-old로 변경
git branch -m main main-old

# main-cleaned를 main으로 변경
git branch -m main-cleaned main

# 이전 main 삭제
git branch -D main-old
# 출력: Deleted branch main-old (was 33cbee3).
```
**결과**: 이제 정리된 히스토리를 가진 main 브랜치 사용

---

## 마무리 작업

### 최종 Push
```bash
git push --force origin main
# 출력: 779b19b..7769e8a main -> main
```
**성공!** 🎉
- `--force` 필요 이유: 히스토리가 변경되어 일반 push는 거부됨

### 임시 파일 정리
```bash
# 토큰 파일 삭제
rm passwords.txt

# Mirror 리포지토리 삭제
rm -rf ../PTCGPBKor.git

# BFG remote 제거
git remote remove bfg
```

---

## 요약 및 교훈

### 전체 프로세스 흐름
1. **문제 발견**: GitHub push protection이 secret 차단
2. **백업 생성**: 안전을 위한 전체 백업
3. **Interactive rebase 시도**: 너무 복잡해서 포기
4. **Filter-branch**: `.env.test` 제거 성공
5. **추가 문제**: 하드코딩된 토큰 발견
6. **코드 수정**: 토큰을 환경변수로 변경
7. **BFG 사용**: 전체 히스토리에서 토큰 제거
8. **성공적인 Push**: 깨끗한 히스토리로 GitHub 업데이트

### 중요한 교훈
1. **Secret은 절대 커밋하지 말 것**: 한 번 커밋되면 제거가 매우 어려움
2. **환경변수 사용**: 민감한 정보는 항상 환경변수로
3. **백업의 중요성**: 히스토리 수정 전 반드시 백업
4. **BFG > filter-branch**: 더 빠르고 안전하고 사용하기 쉬움

### 다음 단계
- ⚠️ **중요**: Discord Developer Portal에서 봇 토큰 재생성 필요
- 모든 봇 파일이 환경변수를 사용하는지 재확인
- .gitignore에 .env* 패턴 확인