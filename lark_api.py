# -*- coding: utf-8 -*-
import requests
import json
import time
from lark_config import *

class LarkBaseAPI:
    def __init__(self):
        self.access_token = None
        
    def get_tenant_access_token(self):
        """Lấy tenant access token từ Lark"""
        url = LARK_TENANT_ACCESS_TOKEN_URL
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": LARK_APP_ID,
            "app_secret": LARK_APP_SECRET
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if result.get("code") == 0:
            self.access_token = result.get("tenant_access_token")
            print("Lay access token thanh cong")
            return True
        else:
            print(f"Loi lay access token: {result}")
            return False
    
    def get_stores_list(self):
        """Lấy danh sách cửa hàng từ Lark Base"""
        if not self.access_token:
            if not self.get_tenant_access_token():
                return []
        
        url = LARK_LIST_RECORDS_URL.format(
            app_token=LARK_BASE_TOKEN,
            table_id=LARK_TABLE_ID
        )
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        all_stores = []
        page_token = None
        
        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get("code") != 0:
                print(f"Loi lay danh sach cua hang: {result}")
                break
            
            records = result.get("data", {}).get("items", [])
            for record in records:
                fields = record.get("fields", {})
                store_info = {
                    "record_id": record.get("record_id"),
                    "store_name": fields.get("Cửa hàng", ""),
                    "link_map": fields.get("Link map", "")
                }
                all_stores.append(store_info)
            
            page_token = result.get("data", {}).get("page_token")
            if not page_token:
                break
        
        print(f"Da lay {len(all_stores)} cua hang tu Lark Base")
        return all_stores
    
    def get_existing_reviews(self):
        """Lấy tất cả Review_ID đã có trong Lark Base để check trùng"""
        if not self.access_token:
            if not self.get_tenant_access_token():
                return {}
        
        url = LARK_LIST_RECORDS_URL.format(
            app_token=LARK_BASE_TOKEN,
            table_id=LARK_TABLE_REVIEW_ID
        )
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        existing_reviews = {}
        page_token = None
        
        print("Dang kiem tra reviews da ton tai trong Lark Base...")
        
        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token
            
            try:
                response = requests.get(url, headers=headers, params=params)
                result = response.json()
                
                if result.get("code") != 0:
                    print(f"Loi lay danh sach reviews: {result}")
                    break
                
                records = result.get("data", {}).get("items", [])
                
                for record in records:
                    fields = record.get("fields", {})
                    review_id = fields.get("Review ID", "")
                    if review_id and review_id != "N/A":
                        existing_reviews[review_id] = record.get("record_id")
                
                page_token = result.get("data", {}).get("page_token")
                if not page_token:
                    break
                    
            except Exception as e:
                print(f"Exception khi lay reviews: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"Tim thay {len(existing_reviews)} reviews da ton tai")
        return existing_reviews
    
    def upsert_reviews(self, reviews_list):
        """
        Update or Create reviews dựa trên Review_ID
        - Nếu Review_ID đã tồn tại -> UPDATE
        - Nếu Review_ID chưa có -> CREATE
        """
        if not reviews_list:
            return {"created": 0, "updated": 0, "failed": 0, "skipped": 0}
        
        print(f"\n=== UPSERT ===")
        print(f"Tong so reviews can xu ly: {len(reviews_list)}")
        
        # Lấy danh sách reviews đã có
        existing_reviews = self.get_existing_reviews()
        
        to_create = []
        to_update = []
        skipped = 0
        
        # Phân loại reviews cần create vs update
        for review in reviews_list:
            review_id = review.get("Review ID", "")
            
            is_empty = not review_id
            is_na = review_id == "N/A"
            
            if is_empty or is_na:
                skipped += 1
                continue
            
            if review_id in existing_reviews:
                # Đã tồn tại -> update
                review["_record_id"] = existing_reviews[review_id]
                to_update.append(review)
            else:
                # Chưa có -> create
                to_create.append(review)
        
        print(f"Phan loai: {len(to_create)} moi, {len(to_update)} cap nhat, {skipped} bo qua")
        
        # Thực hiện CREATE (batch)
        created_count = 0
        if to_create:
            print(f"Dang tao {len(to_create)} reviews moi...")
            created_count = self._batch_create_reviews(to_create)
        
        # Thực hiện UPDATE (batch)
        updated_count = 0
        if to_update:
            print(f"Dang update {len(to_update)} reviews...")
            updated_count = self._batch_update_reviews(to_update)
        
        failed = len(reviews_list) - created_count - updated_count - skipped
        
        return {
            "created": created_count,
            "updated": updated_count,
            "failed": failed,
            "skipped": skipped
        }
    
    def _batch_create_reviews(self, reviews_list):
        """Batch create reviews - tối đa 500 records/lần"""
        url = LARK_BATCH_CREATE_URL.format(
            app_token=LARK_BASE_TOKEN,
            table_id=LARK_TABLE_REVIEW_ID
        )
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        batch_size = 500
        total_created = 0
        
        for i in range(0, len(reviews_list), batch_size):
            batch = reviews_list[i:i + batch_size]
            
            records = []
            for review in batch:
                records.append({
                    "fields": {
                        "Cửa hàng": review.get("Cửa hàng", ""),
                        "Review ID": review.get("Review ID", ""),
                        "Tên người review": review.get("Tên người review", ""),
                        "Xếp hạng": review.get("Xếp hạng", ""),
                        "Thời gian đăng": review.get("Thời gian đăng", ""),
                        "Bài viết": review.get("Bài viết", "")
                    }
                })
            
            payload = {"records": records}
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                result = response.json()
                
                if result.get("code") == 0:
                    created = len(result.get("data", {}).get("records", []))
                    total_created += created
                    print(f"  + Tao thanh cong {created} reviews (batch {i//batch_size + 1})")
                else:
                    print(f"  - Loi tao batch: {result}")
            except Exception as e:
                print(f"  - Loi khi goi API: {e}")
                import traceback
                traceback.print_exc()
        
        return total_created
    
    def _batch_update_reviews(self, reviews_list):
        """Batch update reviews - update từng record một vì Lark API không hỗ trợ batch update tốt"""
        total_updated = 0
        
        print(f"  Dang update {len(reviews_list)} reviews (tung record)...")
        
        for review in reviews_list:
            record_id = review.get("_record_id")
            if not record_id:
                continue
                
            url = LARK_UPDATE_RECORD_URL.format(
                app_token=LARK_BASE_TOKEN,
                table_id=LARK_TABLE_REVIEW_ID,
                record_id=record_id
            )
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=utf-8"
            }
            
            payload = {
                "fields": {
                    "Cửa hàng": review.get("Cửa hàng", ""),
                    "Review ID": review.get("Review ID", ""),
                    "Tên người review": review.get("Tên người review", ""),
                    "Xếp hạng": review.get("Xếp hạng", ""),
                    "Thời gian đăng": review.get("Thời gian đăng", ""),
                    "Bài viết": review.get("Bài viết", "")
                }
            }
            
            try:
                response = requests.put(url, headers=headers, json=payload)
                result = response.json()
                
                if result.get("code") == 0:
                    total_updated += 1
                    if total_updated % 10 == 0:
                        print(f"    + Da update {total_updated}/{len(reviews_list)} reviews...")
                else:
                    print(f"  - Loi update record {record_id}: {result}")
            except Exception as e:
                print(f"  - Loi khi update record {record_id}: {e}")
            
            # Tránh rate limit
            time.sleep(0.1)
        
        print(f"  + Update thanh cong {total_updated}/{len(reviews_list)} reviews")
        return total_updated

if __name__ == "__main__":
    lark = LarkBaseAPI()
    stores = lark.get_stores_list()
    
    if stores:
        print("\nDanh sach cua hang:")
        for i, store in enumerate(stores, 1):
            print(f"{i}. {store['store_name']} - {store['link_map']}")