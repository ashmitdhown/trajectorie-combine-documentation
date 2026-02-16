# AIO Integration Guide

**For:** AIO Development Team  
**Purpose:** What Cogniview will send to AIO and what AIO must provide

---

## Configuration Required

**INTEGRATION_SECRET:** (Used for JWT validation)
**EXTERNAL_AUTH_TOKEN:** (Your static Bearer token used for authorization)

**Base URL:**
Provide your AIO base URL to Cogniview team (e.g., `https://aio-system.com`)

**JWT Token Format:**
When generating `auth_token` for user launch, include these fields:
```json
{
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "iat": 1737964638,
  "exp": 1737965538
}
```
- **Expiry:** 15 minutes from issuance
- **Algorithm:** HS256

---

## What Cogniview Sends to AIO

### 1. Test Metadata (When Test Created)

**Cogniview calls:**
```
POST {AIO_BASE_URL}/api/TestSystem/CreateCogniviewTest
Content-Type: application/json
Authorization: Bearer {EXTERNAL_AUTH_TOKEN}
```

**You receive:**
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

**Complete schema:** `schemas/test_metadata_sync.json`

**You must return:**
```json
{
  "success": true,
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "message": "Test metadata received successfully"
}
```

**Error (if data invalid):**
```json
{
  "success": false,
  "detail": "Invalid test metadata format or missing required fields"
}
```

---

### 2. Test Results (When User Completes Test)

**Cogniview calls:**
```
POST {AIO_BASE_URL}/api/TestSystem/SubmitCogniviewResult
Content-Type: application/json
Authorization: Bearer {EXTERNAL_AUTH_TOKEN}
```

**You receive:**
```json
{
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "completion_status": "COMPLETED",
  "total_score_obtained": 40,
  "detailed_response": [
    {
      "competency_id": "COMP_LEAD",
      "competency_name": "Leadership Excellence",
      "sub_competencies": [
        {
          "sub_competency_id": "APRCNCUST_LVL1",
          "sub_competency_name": "Appreciation of Customer Needs",
          "marks_obtained_sub_competency": 8,
          "time_taken_sec": 205,
          "questions": [
            {
              "question_id": "0235cfbb-af34-409b-a420-bb9a5ccf18dd",
              "time_taken_sec": 95
            }
          ]
        }
      ]
    }
  ]
}
```

**Complete schema:** `schemas/test_results_submission.json`

**You must return:**
```json
{
  "success": true,
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "message": "Results received successfully"
}
```

**Error (if data invalid):**
```json
{
  "success": false,
  "detail": "Invalid results data format or missing required fields"
}
```

---

## What AIO Sends to Cogniview

### User Launch (When User Clicks "Attempt Test")

**You call:**
```
POST https://trajectorie.onrender.com/api/integration/test-launch
Content-Type: application/json
```

**You send:**
```json
{
  "user_id": "EMP_789",
  "user_name": "johndoe123",
  "first_name": "John",
  "last_name": "Doe",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "return_url": "https://aio-system.com/dashboard"
}
```

**Complete schema:** `schemas/test_launch_request.json`

**Notes:**
- `auth_token`: JWT token with user_id and test_id (expires in 15 mins)
- `return_url`: Where user returns after completing test

**Cogniview returns (success):**
```json
{
  "success": true,
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "redirect_url": "https://trajectorie.onrender.com/load_quiz",
  "message": "User authenticated successfully"
}
```

**After receiving success:**
User must be redirected to `redirect_url` using:
- **Method:** POST (required - Cogniview rejects GET)
- **Content-Type:** application/x-www-form-urlencoded
- **Parameter:** `test_name` with value = `test_id`

**Possible errors:** See `schemas/test_launch_errors.json`

---

## Summary

### Endpoints AIO Must Implement:
1. `POST /api/TestSystem/CreateCogniviewTest` - Receives test configuration
2. `POST /api/TestSystem/SubmitCogniviewResult` - Receives test results

### Endpoint AIO Calls:
1. `POST /api/integration/test-launch` - Launches user to Cogniview

### Data Schemas:
All complete JSON examples in `schemas/` folder


