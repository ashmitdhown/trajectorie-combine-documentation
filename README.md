# Cogniview AIO Integration Documentation

**Version:** 1.0 Final  
**Last Updated:** January 28, 2026  

---

## 📁 Documentation Structure

```
integration_docs/
├── README.md                      ← You are here
├── API_OVERVIEW.md                ← Complete API reference
├── AIO_IMPLEMENTATION_GUIDE.md    ← What AIO team must build
└── schemas/                       ← JSON examples (7 files)
    ├── test_metadata_sync.json
    ├── test_launch_request.json
    ├── test_launch_success.json
    ├── test_launch_errors.json
    ├── test_results_submission.json
    └── error_responses.json
```

---

### **For AIO Team**

1. **Read:** `AIO_IMPLEMENTATION_GUIDE.md`
2. **Review:** `schemas/` folder for exact JSON formats
3. **Build:** 2 endpoints (receive metadata & results)
4. **Implement:** User launch flow with JWT + POST redirect

**What to Build:**
- Endpoint to receive test metadata from Cogniview
- Endpoint to receive test results from Cogniview
- User launch flow (generate JWT → POST to Cogniview → redirect user)

---

### **For Cogniview Team**

1. **Implement:** `/api/integration/test-launch` endpoint
2. **Implement:** Results sending to AIO after test submission
3. **Configure:** `AIO_INTEGRATION_SECRET` environment variable
4. **Test:** Integration with AIO team

---

## 🔄 Integration Flow

### **3 Handshakes**

**1. Test Metadata Sync** (Cogniview → AIO)
- **When:** Admin creates/updates test
- **Endpoint:** `POST {AIO}/api/receive-test-metadata`
- **JSON:** `test_metadata_sync.json`

**2. Test Launch** (AIO → Cogniview → User)
- **When:** User clicks "Attempt Test"
- **Flow:**
  1. AIO generates JWT token
  2. AIO POSTs to `{COGNIVIEW}/api/integration/test-launch`
  3. Cogniview validates, returns `redirect_url`
  4. AIO redirects user via POST form
  5. User takes test
- **JSONs:** `test_launch_request.json`, `test_launch_success.json`

**3. Results Submission** (Cogniview → AIO)
- **When:** User submits test
- **Endpoint:** `POST {AIO}/api/receive-test-results`
- **JSON:** `test_results_submission.json`

---

## 🔐 Authentication

**Method:** JWT with shared secret

Both systems must set:
```bash
AIO_INTEGRATION_SECRET=your-matching-secret-key
```

**Token Generation (AIO):**
```python
import jwt
from datetime import datetime, timedelta

token = jwt.encode({
    'user_id': user_id,
    'test_id': test_id,
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(minutes=15)
}, AIO_INTEGRATION_SECRET, algorithm='HS256')
```

---

## ⚠️ Critical Implementation Detail

### **User Redirect MUST Use POST**

After receiving success from Cogniview, AIO must redirect user via **POST form**:

```html
<form method="POST" action="https://trajectorie.onrender.com/load_quiz">
  <input type="hidden" name="test_name" value="test-id-here">
</form>
<script>
  document.getElementById('form-id').submit();
</script>
```

**Why?** Cogniview's `load_quiz` requires POST with `test_name` parameter.

---

## 📊 JSON Schemas

All JSONs in `schemas/` are **direct examples** (not schema markup).

| File | Purpose |
|------|---------|
| `test_metadata_sync.json` | Test config sent to AIO |
| `test_launch_request.json` | Launch request from AIO |
| `test_launch_success.json` | Launch success response |
| `test_launch_errors.json` | Launch error responses |
| `test_results_submission.json` | Results sent to AIO |
| `error_responses.json` | All other errors |

---

## 📝 Error Format

All errors follow:

```json
{
  "success": false,
  "detail": "Error message here"
}
```

---

## 🌐 Base URL

**Current (Render):**
```
https://trajectorie.onrender.com
```

**Future (GoDaddy):**
```
https://your-domain.com
```

**Migration Impact:** Only base URL changes. No code changes needed.

---

## What AIO Must Build

1. **2 Endpoints:**
   - `POST /api/receive-test-metadata`
   - `POST /api/receive-test-results`

2. **User Launch Flow:**
   - Generate JWT token
   - POST to Cogniview test-launch endpoint
   - Redirect user via POST form

3. **Data Storage:**
   - Test metadata (competencies, questions)
   - Test results (scores, time tracking)

---

## What Cogniview Must Build

1. **1 Endpoint:**
   - `POST /api/integration/test-launch`

2. **Results Sending:**
   - After test submission, POST to AIO results endpoint

3. **Session Management:**
   - Create session from AIO user data
   - Store `return_url` for post-test redirect

---

## 🧪 Testing

1. AIO generates token and sends launch request
2. Cogniview validates and returns redirect URL
3. User redirects to Cogniview via POST form
4. User sees instructions → starts test → completes
5. Results sent to AIO
6. User redirects back to AIO dashboard

