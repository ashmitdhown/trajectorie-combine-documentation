# AIO Integration - Implementation Guide

**For:** AIO Development Team  
**Purpose:** Complete checklist of what to build

---

## 🔧 Configuration

1. Set environment variable:
   ```bash
   AIO_INTEGRATION_SECRET=your-shared-secret-key
   ```
   **Important:** Must match Cogniview's secret exactly

2. Install JWT library:
   - Python: `pip install PyJWT`
   - Node.js: `npm install jsonwebtoken`

3. Configure base URLs:
   - Your AIO base URL (e.g., `https://aio-system.com`)
   - Cogniview base URL: `https://trajectorie.onrender.com`

---

## 📋 Endpoints to Implement

### 1. Receive Test Metadata

```
POST /api/receive-test-metadata
Content-Type: application/json
```

**When:** Cogniview sends this when admin creates/updates test

**Receives:** See `schemas/test_metadata_sync.json`

**Must Store:**
- Test configuration (id, name, duration, mode, total marks)
- Competency hierarchy
- Question metadata

**Must Return:**
```json
{
  "success": true,
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "message": "Test metadata received successfully"
}
```

---

### 2. Receive Test Results

```
POST /api/receive-test-results
Content-Type: application/json
```

**When:** Cogniview sends this after user completes test

**Receives:** See `schemas/test_results_submission.json`

**Must Store:**
- Overall test score
- Competency-wise scores
- Sub-competency scores
- Question-level time tracking

**Must Return:**
```json
{
  "success": true,
  "user_id": "EMP_789",
  "test_id": "test-id",
  "message": "Results received successfully"
}
```

---

## 🚀 User Launch Flow

### When User Clicks "Attempt Test"

**Step 1: Generate JWT Token**

```python
import jwt
from datetime import datetime, timedelta

def generate_test_launch_token(user_id, test_id):
    payload = {
        'user_id': user_id,
        'test_id': test_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=15)
    }
    return jwt.encode(payload, AIO_INTEGRATION_SECRET, algorithm='HS256')
```

**Step 2: Send Launch Request**

```python
import requests

response = requests.post(
    'https://trajectorie.onrender.com/api/integration/test-launch',
    json={
        'user_id': 'EMP_789',
        'user_name': 'johndoe123',
        'first_name': 'John',
        'last_name': 'Doe',
        'test_id': '06fc6856-dc27-4756-a296-bca09272701c',
        'auth_token': token,
        'return_url': 'https://aio-system.com/dashboard'
    }
)

if response.status_code == 200:
    data = response.json()
    redirect_url = data['redirect_url']
    test_id = data['test_id']
    # Proceed to step 3
else:
    # Handle error
    error = response.json()
    print(error['detail'])
```

**Step 3: Redirect User via POST Form**

**CRITICAL:** Must use POST form (not GET redirect)

```html
<!-- Auto-submit form to redirect user -->
<form method="POST" action="{{ redirect_url }}" id="launchForm">
  <input type="hidden" name="test_name" value="{{ test_id }}">
</form>
<script>
  document.getElementById('launchForm').submit();
</script>
```

**Why POST?** Cogniview's `load_quiz` endpoint requires POST with `test_name` parameter.

---

## 📊 Data Formats

### Test Metadata Example
```json
{
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "test_name": "Senior Management Assessment",
  "duration_min": 45,
  "number_of_questions": 30,
  "mode": "assessment",
  "total_marks": 144,
  "competencies": [...],
  "questions": [...]
}
```

### Test Results Example
```json
{
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "completion_status": "COMPLETED",
  "total_score_obtained": 40,
  "detailed_response": [...]
}
```

See `schemas/` folder for complete examples.

---

## ⚠️ Important Rules

1. **POST Form Redirect** - User must be redirected via POST (not GET)
2. **JWT Expiration** - Tokens expire in 15 minutes
3. **Shared Secret** - Must match Cogniview's secret exactly
4. **HTTPS Only** - All requests must use HTTPS in production
5. **Return URL** - User returns here after completing test

---

## ✅ Testing Checklist

- [ ] Can receive and store test metadata
- [ ] Can receive and store test results
- [ ] Can generate valid JWT tokens
- [ ] Can POST launch request to Cogniview
- [ ] User successfully redirects to Cogniview (POST form)
- [ ] User sees test instructions
- [ ] User completes test
- [ ] Results received in AIO
- [ ] User redirects back to AIO dashboard

