# Lark Base Configuration
LARK_APP_ID = "cli_a8620f964a38d02f"
LARK_APP_SECRET = "G3FdlSvmTAXZYX8SBZtfpckHUiWUCO4h"
LARK_BASE_TOKEN = "VLMUbLONpaIWT1sVuQ7lt6lpgn3"
LARK_TABLE_ID = "tbld7PZ0yY7lUOOg"
LARK_TABLE_REVIEW_ID = "tblAoE2I2Syh7q18"

# API Endpoints
LARK_API_BASE = "https://open.larksuite.com/open-apis"
LARK_TENANT_ACCESS_TOKEN_URL = f"{LARK_API_BASE}/auth/v3/tenant_access_token/internal"
LARK_LIST_RECORDS_URL = f"{LARK_API_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records"
LARK_CREATE_RECORD_URL = f"{LARK_API_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records"
LARK_UPDATE_RECORD_URL = f"{LARK_API_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records/{{record_id}}"
LARK_BATCH_CREATE_URL = f"{LARK_API_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records/batch_create"
LARK_BATCH_UPDATE_URL = f"{LARK_API_BASE}/bitable/v1/apps/{{app_token}}/tables/{{table_id}}/records/batch_update"