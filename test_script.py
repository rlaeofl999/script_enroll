import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re

# ==========================================
# 1. 파일 및 경로 설정
# ==========================================
# 원본 엑셀 파일 경로 (파일명과 경로가 맞는지 꼭 확인하세요)
file_path = r"C:\TEST.xlsx" 
current_folder = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(file_path):
    print(f"❌ 에러: {file_path} 경로에 파일이 없습니다.")
    exit()

try:
    df = pd.read_excel(file_path, engine='openpyxl')
    df.columns = df.columns.str.strip() # 컬럼명 공백 제거
    print(f"✅ 엑셀 로드 성공! 총 {len(df)}명의 데이터를 분석합니다.")
except Exception as e:
    print(f"❌ 엑셀 로드 실패: {e}")
    exit()

# ==========================================
# 2. 브라우저 실행 및 환경 설정
# ==========================================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# 속도를 위해 불필요한 로그 끄기
options.add_experimental_option("excludeSwitches", ["enable-logging"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

results = []

try:
    for index, row in df.iterrows():
        # [핵심] 이전 환자 데이터 잔상 제거를 위해 매번 페이지 새로고침
        driver.get("https://bostonmontpelliercare.shinyapps.io/AIClarity/")
        time.sleep(10) # Shiny 서버 초기 로딩 대기 (중요)

        p_id = str(row.get('연구내원번호', index + 1))
        print(f"\n>>> [{index + 1}/{len(df)}] 환자번호: {p_id} 입력 시작...")

        # 데이터 매핑 (사이트 라벨 : 엑셀 컬럼명)
        mapping = {
            "Bilirubin": row.get('Bilirubin'),
            "Creatinine": row.get('Creatinine'),
            "Albumin": row.get('Albumin'),
            "Glucose": row.get('Glucose'),
            "Sodium": row.get('Na'),
            "Hematocrit": row.get('Hematocrit'),
            "White blood cell count": row.get('WBC'),
            "Platelet": row.get('Platelets'),
            "PaCO2": row.get('PaCO2'),
            "PaO2/FiO2 ratio": row.get('PaO/FiO ratio'),
            "Temperature": row.get('BT'),
            "Respiratory rate": row.get('Respiratory rate'),
            "Heart rate": row.get('Heart rate'),
            "Systolic blood pressure": row.get('Systolic blood pressure'),
            "Bicarbonate": row.get('Bicarbonate')
        }

        # A. 수치 데이터 입력
        for label_text, val in mapping.items():
            if pd.notnull(val) and str(val).strip().lower() != "nan" and str(val).strip() != "":
                try:
                    xpath = f"//label[contains(text(), '{label_text}')]/following-sibling::input"
                    field = driver.find_element(By.XPATH, xpath)
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
                    field.clear()
                    field.send_keys(str(val))
                except:
                    pass

        # B. Vasopressors 선택
        try:
            v_col = 'Vasopressors (Use of vasopressors?)'
            choice = str(row.get(v_col, 'No')).strip()
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
        except:
            print("    - Vasopressors 선택 건너뜀")

        # C. Predict 버튼 클릭
        print("    - Prediction 요청 중...", end="", flush=True)
        try:
            driver.execute_script("document.getElementById('go').click();")
        except:
            try:
                driver.execute_script("document.querySelector('button.btn-primary').click();")
            except:
                print(" 버튼 클릭 실패", end="")
        print(" 완료")

        # D. 결과 추출 (정규식 기반 무한 집착 로직)
        final_res = "N/A"
        print("    - 결과 대기 중", end="", flush=True)
        
        for i in range(25): # 최대 50초 대기
            time.sleep(2)
            print(".", end="", flush=True)
            try:
                # 화면 전체 텍스트에서 '숫자 %' 패턴 찾기
                page_text = driver.execute_script("return document.body.innerText;")
                match = re.search(r'(\d+\.?\d*\s?%)', page_text)
                
                if match:
                    final_res = match.group(1)
                    break
                
                # 10초 지났는데 결과 안 나오면 버튼 한 번 더 클릭
                if i == 5:
                    driver.execute_script("document.getElementById('go').click();")
            except:
                pass
        
        print(f" => {final_res}")
        results.append(final_res)

        # [옵션] 10명마다 중간 저장 (혹시 모를 오류 대비)
        if (index + 1) % 10 == 0:
            temp_df = df.iloc[:len(results)].copy()
            temp_df['Probability_Result'] = results
            temp_df.to_excel(os.path.join(current_folder, "BACKUP_CURRENT.xlsx"), index=False)

    # ==========================================
    # 3. 최종 저장 (PermissionError 방지)
    # ==========================================
    timestr = time.strftime("%Y%m%d-%H%M%S")
    # 파일명에 시간을 붙여서 덮어쓰기 권한 문제 원천 차단
    final_save_path = os.path.join(current_folder, f"RESULT_{timestr}.xlsx")
    
    df['Probability_Result'] = results
    df.to_excel(final_save_path, index=False)
    print(f"\n✨🎉 대성공! 모든 작업이 완료되었습니다.")
    print(f"📂 결과 파일 저장 위치: {final_save_path}")

except Exception as e:
    print(f"\n❌ 실행 중 치명적 에러 발생: {e}")

finally:
    print("\n브라우저를 종료합니다.")
    driver.quit()