# script_enroll

스크립트 관리 및 효율적인 버전 제어를 위한 가이드라인입니다.

</br>

## 🚀 사용법 (Usage)

### 1. 변경 사항 저장
로컬에서 작업한 내용을 저장소에 기록할 때 사용합니다.
-> 변경된 모든 파일 추가

```bash
git add .
```

### 2. 커밋
변경 내용에 대한 메시지 기록

```bash
git commit -m "메세지 내용"
```

### 3. 원격 저장소에 올리기
내 컴퓨터의 변경 사항을 GitHub 서버로 업로드합니다.

```bash
git push
```

### 4. 다른 사람의 변경 사항 내려받기
동료가 작업한 최신 코드를 내 컴퓨터로 가져옵니다.

```bash
# 원격 저장소의 최신 이력 확인
git fetch

# 특정 브랜치의 내용을 가져와서 병합
git pull origin 브랜치이름
```

### 5. 라이브러리 설치
공통된 작업환경을 위해 가상환경 및 라이브러리를 설치합니다.

```bash
uv sync
```

### 6. 파일 실행
uv를 사용하여 파일을 실행합니다.

```bash
uv run 파일명
```

</br>

## 문제 해결 (Troubleshooting)

### 1. Windows 환경에서 줄바꿈 관련 에러 발생 시
Windows에서 git add 시 다음과 같은 경고 문구가 뜨는 경우가 있습니다.
warning: LF will be replaced by CRLF in (파일경로)...

#### 원인
운영체제마다 줄바꿈(Line Ending)을 처리하는 방식이 다르기 때문에 발생하는 현상입니다.

- Windows: CRLF (\r\n)
- Mac / Linux: LF (\n)

#### 해결 방법 (Windows)
아래 명령어를 입력하면 Git이 자동으로 줄바꿈 문자를 변환해 주어 에러를 해결할 수 있습니다.
```bash
git config core.autocrlf true
```
