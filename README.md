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

## 📖 main.py 사용법

AIClarity 웹앱에 환자 데이터를 자동 입력하고 예측 결과(Probability)를 수집하는 스크립트입니다.

### 실행

```bash
uv run main.py
```

### 실행 흐름

1. **파일 선택** - 팝업 창에서 분석할 엑셀 파일(.xlsx)을 선택합니다.
2. **구간 설정** - 시작 행과 끝 행 번호를 입력합니다. (기본값: 전체)
3. **자동 처리** - 각 환자 데이터를 웹앱에 입력하고 결과를 수집합니다.
4. **결과 저장** - 완료 시 `RESULT_파일명_시작_끝_날짜.xlsx` 파일이 생성됩니다.

### 엑셀 파일 필수 컬럼

| 컬럼명 | 설명 |
|---|---|
| Bilirubin | 빌리루빈 |
| Creatinine | 크레아티닌 |
| Albumin | 알부민 |
| Glucose | 혈당 |
| Na | 나트륨 |
| Hematocrit | 헤마토크릿 |
| WBC | 백혈구 수 |
| Platelets | 혈소판 |
| PaCO2 | 이산화탄소 분압 |
| PaO/FiO ratio | PaO2/FiO2 비율 |
| BT | 체온 |
| Respiratory rate | 호흡수 |
| Heart rate | 심박수 |
| Systolic blood pressure | 수축기 혈압 |
| Urine output | 소변량 |
| Minute Ventilation | 분당 환기량 |
| Bicarbonate | 중탄산염 |
| Vasopressors (Use of vasopressors?) | 승압제 사용 여부 (Yes/No) |

### 대량 데이터 처리 (배치)

6000명 등 대량 데이터는 구간을 나눠서 처리하는 것을 권장합니다.

```
1회차: 시작 1, 끝 1000
2회차: 시작 1001, 끝 2000
3회차: 시작 2001, 끝 3000
...
```

또는 엑셀 파일 자체를 나눠서 각각 실행해도 됩니다. (같은 폴더에 있어도 OK)

### 중단 & 이어하기 (Resume)

- 매 환자 처리 완료 시 **백업 파일**(`BACKUP_파일명_시작_끝.xlsx`)이 자동 저장됩니다.
- 중간에 크래시나 강제 종료가 발생해도, **같은 파일 + 같은 구간**으로 다시 실행하면 이미 완료된 환자는 건너뛰고 이어서 진행합니다.
- 모든 처리가 정상 완료되면 백업 파일은 자동 삭제됩니다.

### 생성되는 파일

| 파일 | 설명 | 시점 |
|---|---|---|
| `BACKUP_파일명_시작_끝.xlsx` | 중간 저장 (resume용) | 매 환자 완료 시 |
| `RESULT_파일명_시작_끝_날짜.xlsx` | 최종 결과 | 전체 완료 시 |

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
