from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import os
from datetime import datetime

def create_safe_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
       
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("Driver khoi tao thanh cong")
        return driver
    except Exception as e:
        print(f"Loi tao driver: {e}")
        return None

if __name__ == "__main__":
    os.makedirs('data', exist_ok=True)
    
    url = "https://maps.app.goo.gl/qqXVahqHf1hedADm7"
    driver = create_safe_driver()
    
    if driver:
        try:
            print(f"Dang mo link...")
            driver.get(url)
            time.sleep(2)
            
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.GQjSyb.fontTitleSmall.rqjGif"))
            )
            driver.execute_script("arguments[0].click();", button)
            print("Da click reviews button")
            time.sleep(2)
            
            print("Dang scroll load reviews...")
            try:
                scrollable_div = driver.find_element(By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf")
            except:
                scrollable_div = driver.find_element(By.XPATH, "//div[@role='feed']")
            
            last_height = 0
            no_change = 0
            
            while no_change < 3:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                time.sleep(1.5)
                
                current_reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf.fontBodyMedium")
                new_height = len(current_reviews)
                
                if new_height == last_height:
                    no_change += 1
                else:
                    no_change = 0
                    print(f"Da load {new_height} reviews")
                
                last_height = new_height
            
            print(f"Hoan thanh scroll. Tong: {last_height} reviews\n")
            
            reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf.fontBodyMedium")
            reviews_data = []
            
            for index, review in enumerate(reviews, 1):
                try:
                    reviewer_name = review.find_element(By.CSS_SELECTOR, "div.d4r55.fontTitleMedium").text if review.find_elements(By.CSS_SELECTOR, "div.d4r55.fontTitleMedium") else "N/A"
                    
                    rating_element = review.find_element(By.CSS_SELECTOR, "span.kvMYJc") if review.find_elements(By.CSS_SELECTOR, "span.kvMYJc") else None
                    rating = rating_element.get_attribute("aria-label") if rating_element else "N/A"
                    
                    time_posted = review.find_element(By.CSS_SELECTOR, "span.rsqaWe").text if review.find_elements(By.CSS_SELECTOR, "span.rsqaWe") else "N/A"
                    
                    review_text = review.find_element(By.CSS_SELECTOR, "span.wiI7pd").text if review.find_elements(By.CSS_SELECTOR, "span.wiI7pd") else ""
                    
                    review_id = review.get_attribute("data-review-id") or "N/A"
                    
                    reviews_data.append({
                        "STT": index,
                        "Review_ID": review_id,
                        "Reviewer_Name": reviewer_name,
                        "Rating": rating,
                        "Time_Posted": time_posted,
                        "Review_Text": review_text
                    })
                    
                except Exception as e:
                    print(f"Loi review #{index}: {e}")
            
            print(f"Tong cong: {len(reviews_data)} reviews\n")
            
            df = pd.DataFrame(reviews_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/google_maps_reviews_{timestamp}.xlsx"
            
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"Da luu thanh cong: {filename}")
            print(f"\nPreview 5 reviews dau:\n{df.head()}")
            
        except Exception as e:
            print(f"Loi: {e}")
            import traceback
            traceback.print_exc()
        finally:
            driver.quit()
            print("\nDa dong trinh duyet")
    else:
        print("Khong the tao driver!")