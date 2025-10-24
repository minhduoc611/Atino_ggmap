# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from datetime import datetime
from lark_api import LarkBaseAPI

def create_safe_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Chạy không cần giao diện
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Force tiếng Việt và timezone Việt Nam
        chrome_options.add_argument('--lang=vi-VN')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('prefs', {
            'intl.accept_languages': 'vi-VN,vi,en-US,en',
            'profile.default_content_setting_values.geolocation': 1  # Allow geolocation
        })
       
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set geolocation to Vietnam (Hanoi)
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", {
            "latitude": 21.0285,
            "longitude": 105.8542,
            "accuracy": 100
        })
        
        # Set timezone to Asia/Ho_Chi_Minh (UTC+7)
        driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
            "timezoneId": "Asia/Ho_Chi_Minh"
        })
        
        # Set locale to Vietnamese
        driver.execute_cdp_cmd("Emulation.setLocaleOverride", {
            "locale": "vi-VN"
        })
        
        return driver
    except Exception as e:
        print(f"Loi tao driver: {e}")
        return None

def scrape_store_reviews(driver, store_name, url):
    """Cào reviews cho 1 cửa hàng"""
    try:
        print(f"\n{'='*60}")
        print(f"Dang xu ly: {store_name}")
        print(f"{'='*60}")
        
        # Thêm ?hl=vi vào URL để force tiếng Việt
        if '?' in url:
            url = url + '&hl=vi'
        else:
            url = url + '?hl=vi'
        
        driver.get(url)
        time.sleep(3)
        
        # Cuộn trang để kích hoạt lazy loading
        print("Dang cuon trang de load du lieu...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.5)
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Click button reviews với nhiều selector dự phòng
        button_clicked = False
        
        selectors = [
            "button.GQjSyb.fontTitleSmall.rqjGif",
            "button[aria-label*='bài viết']",
            "button[aria-label*='đánh giá']",
            "button[aria-label*='Reviews']",
            "button[aria-label*='review']",
            "button.fontTitleSmall",
            "//button[contains(@aria-label, 'bài viết')]",
            "//button[contains(@aria-label, 'review')]",
        ]
        
        for selector in selectors:
            try:
                print(f"Thu selector: {selector[:50]}...")
                
                if selector.startswith("//"):
                    button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5)
                
                try:
                    button.click()
                except:
                    driver.execute_script("arguments[0].click();", button)
                
                time.sleep(2)
                button_clicked = True
                print("Da click button reviews thanh cong!")
                break
                
            except Exception as e:
                continue
        
        if not button_clicked:
            print(f"Khong tim thay button reviews cho {store_name}")
            try:
                reviews_section = driver.find_element(By.XPATH, "//div[@role='feed']")
                print("Tim thay phan reviews truc tiep")
            except:
                return []
        
        time.sleep(2)
        
        # Scroll load reviews với nhiều selector dự phòng
        scrollable_div = None
        scroll_selectors = [
            (By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf"),
            (By.XPATH, "//div[@role='feed']"),
            (By.CSS_SELECTOR, "div[role='feed']"),
            (By.CSS_SELECTOR, "div.m6QErb"),
        ]
        
        for by_type, selector in scroll_selectors:
            try:
                scrollable_div = driver.find_element(by_type, selector)
                print(f"Tim thay scrollable div: {selector[:50]}...")
                break
            except:
                continue
        
        if not scrollable_div:
            print(f"Khong tim thay scrollable div cho {store_name}")
            return []
        
        # Scroll load reviews
        last_height = 0
        no_change = 0
        
        print("Dang scroll load reviews...")
        while no_change < 3:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(1.5)
            
            current_reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf.fontBodyMedium")
            new_height = len(current_reviews)
            
            if new_height == last_height:
                no_change += 1
            else:
                no_change = 0
                print(f"  Hien tai: {new_height} reviews...")
            
            last_height = new_height
        
        print(f"Da load {last_height} reviews cho {store_name}")
        
        # Lay thong tin reviews
        reviews = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf.fontBodyMedium")
        reviews_data = []
        
        for index, review in enumerate(reviews, 1):
            try:
                reviewer_name = review.find_element(By.CSS_SELECTOR, "div.d4r55.fontTitleMedium").text if review.find_elements(By.CSS_SELECTOR, "div.d4r55.fontTitleMedium") else "N/A"
                
                rating_element = review.find_element(By.CSS_SELECTOR, "span.kvMYJc") if review.find_elements(By.CSS_SELECTOR, "span.kvMYJc") else None
                rating = rating_element.get_attribute("aria-label") if rating_element else "N/A"
                
                # Convert rating to Vietnamese
                rating = convert_to_vietnamese(rating)
                
                time_posted = review.find_element(By.CSS_SELECTOR, "span.rsqaWe").text if review.find_elements(By.CSS_SELECTOR, "span.rsqaWe") else "N/A"
                
                review_text = review.find_element(By.CSS_SELECTOR, "span.wiI7pd").text if review.find_elements(By.CSS_SELECTOR, "span.wiI7pd") else ""
                
                review_id = review.get_attribute("data-review-id") or f"TEMP_{store_name}_{index}"

                reviews_data.append({
                    "Cửa hàng": store_name,
                    "Review ID": review_id,
                    "Tên người review": reviewer_name,
                    "Xếp hạng": rating,
                    "Thời gian đăng": time_posted,
                    "Bài viết": review_text
                })
                
            except Exception as e:
                print(f"Loi review #{index}: {e}")
        
        print(f"Thu thap duoc {len(reviews_data)} reviews tu {store_name}")
        return reviews_data
        
    except Exception as e:
        print(f"Loi khi xu ly {store_name}: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    lark = LarkBaseAPI()
    print("Dang lay danh sach cua hang tu Lark Base...")
    stores = lark.get_stores_list()
    
    if not stores:
        print("Khong co cua hang nao. Vui long kiem tra cau hinh Lark Base.")
        exit()
    
    print(f"\nBat dau cao reviews cho {len(stores)} cua hang...\n")
    
    driver = create_safe_driver()
    
    if not driver:
        print("Khong the tao driver!")
        exit()
    
    all_reviews = []
    success_count = 0
    total_stats = {"created": 0, "updated": 0, "failed": 0}
    
    try:
        for idx, store in enumerate(stores, 1):
            store_name = store['store_name']
            link_map = store['link_map']
            
            if not link_map:
                print(f"\nBo qua {store_name}: Khong co link map")
                continue
            
            print(f"\n[{idx}/{len(stores)}] Dang xu ly: {store_name}")
            
            reviews = scrape_store_reviews(driver, store_name, link_map)
            
            if reviews:
                all_reviews.extend(reviews)
                success_count += 1
                
                print(f"\nDang dong bo {len(reviews)} reviews vao Lark Base...")
                result = lark.upsert_reviews(reviews)
                
                total_stats["created"] += result["created"]
                total_stats["updated"] += result["updated"]
                total_stats["failed"] += result["failed"]
                
                print(f"Ket qua: {result['created']} tao moi, {result['updated']} cap nhat, {result['failed']} loi")
            
            if idx < len(stores):
                time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"TONG KET:")
        print(f"{'='*60}")
        print(f"Tong cua hang xu ly thanh cong: {success_count}/{len(stores)}")
        print(f"Tong reviews thu thap: {len(all_reviews)}")
        print(f"Reviews tao moi: {total_stats['created']}")
        print(f"Reviews cap nhat: {total_stats['updated']}")
        print(f"Reviews loi: {total_stats['failed']}")
        print(f"{'='*60}\n")
            
    except Exception as e:
        print(f"\nLoi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\nDa dong trinh duyet")


