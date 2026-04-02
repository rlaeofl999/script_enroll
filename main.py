import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import time
import os
import re

# ==========================================
# 1. 파일 선택 UI
# ==========================================
root = tk.Tk()
root.withdraw()  # 메인 창 숨기기

file_path = filedialog.askopenfilename(
    title="분석할 엑셀 파일을 선택하세요",
    filetypes=[("Excel 파일", "*.xlsx *.xls"), ("모든 파일", "*.*")]
)

if not file_path:
    messagebox.showwarning("취소됨", "파일을 선택하지 않았습니다. 프로그램을 종료합니다.")
    exit()

current_folder = os.path.dirname(os.path.abspath(file_path))


try:
    df = pd.read_excel(file_path, engine='openpyxl')
    df.columns = df.columns.str.strip() # 컬럼명 공백 제거
    print(f"✅ 엑셀 로드 성공! 파일: {os.path.basename(file_path)} / 총 {len(df)}명의 데이터를 분석합니다.")
except Exception as e:
    print(f"❌ 엑셀 로드 실패: {e}")
    exit()

# ==========================================
# 1-1. 배치 구간 설정 + Resume
# ==========================================
start_row = simpledialog.askinteger("시작 행", f"시작 행 번호 (1 ~ {len(df)}):", initialvalue=1, minvalue=1, maxvalue=len(df))
end_row = simpledialog.askinteger("끝 행", f"끝 행 번호 (1 ~ {len(df)}):", initialvalue=len(df), minvalue=1, maxvalue=len(df))

if start_row is None or end_row is None:
    messagebox.showwarning("취소됨", "구간을 설정하지 않았습니다. 프로그램을 종료합니다.")
    exit()

start_idx = start_row - 1  # 0-based index
end_idx = end_row           # exclusive

# 기존 백업 파일에서 이미 처리된 결과 로드 (resume)
base_name = os.path.splitext(os.path.basename(file_path))[0]
backup_path = os.path.join(current_folder, f"BACKUP_{base_name}_{start_row}_{end_row}.xlsx")
completed = {}  # index -> result
if os.path.exists(backup_path):
    try:
        backup_df = pd.read_excel(backup_path, engine='openpyxl')
        if 'Probability_Result' in backup_df.columns and '_original_index' in backup_df.columns:
            for _, brow in backup_df.iterrows():
                orig_idx = int(brow['_original_index'])
                res = brow['Probability_Result']
                if pd.notna(res) and str(res).strip() != 'N/A':
                    completed[orig_idx] = str(res)
            print(f"🔄 백업에서 {len(completed)}명의 기존 결과를 로드했습니다. 나머지부터 이어서 진행합니다.")
    except Exception as e:
        print(f"⚠ 백업 로드 실패 (무시하고 처음부터 진행): {e}")

df_batch = df.iloc[start_idx:end_idx]
total_in_batch = len(df_batch)
print(f"📋 처리 구간: {start_row}행 ~ {end_row}행 (총 {total_in_batch}명, 이미 완료: {len(completed)}명, 남은: {total_in_batch - len(completed)}명)")

# ==========================================
# 2. 브라우저 실행 및 환경 설정
# ==========================================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# 브라우저를 숨기려면 아래 줄의 주석을 해제
options.add_argument("--headless")
# 속도를 위해 불필요한 로그 끄기
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

results = {}  # index -> result (resume 포함)
results.update(completed)

def fill_field(driver, field_id, val):
    """주어진 input id에 값을 입력. 값이 없으면 건너뜀."""
    if pd.isnull(val) or str(val).strip().lower() in ("nan", ""):
        return
    try:
        field = driver.find_element(By.ID, field_id)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
        field.clear()
        field.send_keys(str(val))
    except Exception as e:
        print(f"    ⚠ '{field_id}' 입력 실패: {e}")

try:
    for index, row in df_batch.iterrows():
        # 이미 완료된 행은 건너뛰기
        if index in completed:
            print(f"    ⏭ [{index + 1}/{len(df)}] 이미 완료 - 건너뜀")
            continue

        # [핵심] 이전 환자 데이터 잔상 제거를 위해 매번 페이지 새로고침
        driver.get("https://bostonmontpelliercare.shinyapps.io/AIClarity/")
        wait.until(EC.presence_of_element_located((By.ID, "Bilirubin")))  # 첫 입력 필드가 뜰 때까지 대기

        p_id = str(row.get('연구내원번호', index + 1))
        print(f"\n>>> [{index + 1}/{len(df)}] 환자번호: {p_id} 입력 시작...")

        # 데이터 매핑 (사이트 input id : 엑셀 컬럼명)
        # 사이트 HTML의 각 input id와 정확히 일치해야 합니다.
        mapping = {
            "Bilirubin":              row.get('Bilirubin'),
            "Creatinine":             row.get('Creatinine'),
            "Albumin":                row.get('Albumin'),
            "Glucose":                row.get('Glucose'),
            "Sodium":                 row.get('Na'),
            "Hematocrit":             row.get('Hematocrit'),
            "White blood cell count": row.get('WBC'),
            "Platelet":               row.get('Platelets'),
            "PaCO2":                  row.get('PaCO2'),
            "PaO2/FiO2 ratio":        row.get('PaO/FiO ratio'),
            "Temperature":            row.get('BT'),
            "Respiratory rate":       row.get('Respiratory rate'),
            "Heart rate":             row.get('Heart rate'),
            "Systolic blood pressure":row.get('Systolic blood pressure'),
            "Urine output":           row.get('Urine output'),
            "Minute Ventilation":     row.get('Minute Ventilation'),
            "Bicarbonate":            row.get('Bicarbonate'),
        }

        # A. 수치 데이터 입력 (By.ID 사용 - XPath보다 안정적)
        for field_id, val in mapping.items():
            fill_field(driver, field_id, val)

        # B. Vasopressors 선택
        try:
            v_col = 'Vasopressors (Use of vasopressors?)'
            raw = row.get(v_col)
            choice = 'No' if pd.isnull(raw) or str(raw).strip().lower() == 'nan' else str(raw).strip()
            vaso_div = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.selectize-input")))
            driver.execute_script("arguments[0].click();", vaso_div)
            time.sleep(1)
            driver.execute_script(f"""
                var opts = document.querySelectorAll('.option');
                for(var i=0; i<opts.length; i++) {{
                    if(opts[i].innerText.trim() === '{choice}') {{ opts[i].click(); break; }}
                }}
            """)
            print(f"    - Vasopressors: {choice} 선택 완료")
        except Exception as e:
            print(f"    - Vasopressors 선택 실패: {e}")

        # C. Predict 버튼 클릭 (실제 버튼 id: predict_btn)
        print("    - Prediction 요청 중...", end="", flush=True)
        try:
            btn = wait.until(EC.element_to_be_clickable((By.ID, "predict_btn")))
            driver.execute_script("arguments[0].click();", btn)
        except Exception as e:
            try:
                driver.execute_script("document.querySelector('button.btn-primary').click();")
            except Exception as e2:
                print(f" 버튼 클릭 실패: {e} / {e2}", end="")
        print(" 완료")

        # D. 결과 추출 - prediction_output div를 직접 타겟
        final_res = "N/A"
        print("    - 결과 대기 중", end="", flush=True)

        for i in range(25): # 최대 50초 대기
            time.sleep(2)
            print(".", end="", flush=True)
            try:
                # prediction_output div의 텍스트를 직접 읽기
                output_text = driver.execute_script(
                    "return document.getElementById('prediction_output').innerText;"
                )
                match = re.search(r'(\d+\.?\d*\s?%)', output_text or "")

                if match:
                    final_res = match.group(1)
                    break
            except Exception as e:
                print(f"\n    ⚠ 결과 읽기 오류: {e}", end="")

        print(f" => {final_res}")
        results[index] = final_res

        # 매 환자마다 중간 저장 (resume용 백업)
        temp_df = df_batch.copy()
        temp_df['_original_index'] = temp_df.index
        temp_df['Probability_Result'] = temp_df.index.map(results)
        temp_df.to_excel(backup_path, index=False)
        print(f"    💾 저장 완료 ({len(results)}명)")

    # ==========================================
    # 3. 최종 저장 (PermissionError 방지)
    # ==========================================
    timestr = time.strftime("%Y%m%d-%H%M%S")
    final_save_path = os.path.join(current_folder, f"RESULT_{base_name}_{start_row}_{end_row}_{timestr}.xlsx")

    result_df = df_batch.copy()
    result_df['Probability_Result'] = result_df.index.map(results)
    result_df.to_excel(final_save_path, index=False)
    print(f"\n✨🎉 대성공! {start_row}~{end_row}행 작업이 완료되었습니다.")
    print(f"📂 결과 파일 저장 위치: {final_save_path}")

    # 백업 파일 정리
    if os.path.exists(backup_path):
        os.remove(backup_path)
        print("🗑 백업 파일 삭제 완료")

except Exception as e:
    print(f"\n❌ 실행 중 치명적 에러 발생: {e}")

finally:
    print("\n브라우저를 종료합니다.")
    driver.quit()