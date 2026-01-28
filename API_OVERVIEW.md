# Cogniview API Integration Documentation

**Version:** 1.0  
**Last Updated:** January 28, 2026  

---

## Table of Contents

1. [Introduction](#introduction)
2. [Base URL Configuration](#base-url-configuration)
3. [Authentication](#authentication)
4. [Integration Flow](#integration-flow)
5. [Handshake 1: Test Metadata Sync](#handshake-1-test-metadata-sync)
6. [Handshake 2: Test Launch](#handshake-2-test-launch)
7. [Handshake 3: Results Submission](#handshake-3-results-submission)
8. [Error Handling](#error-handling)

---

## Introduction

The Cogniview API enables seamless integration with external Assessment and Interview Orchestration (AIO) systems. This RESTful API facilitates:

- **Test Metadata Synchronization**: Push test configurations from Cogniview to AIO
- **Secure Test Launch**: Users from AIO can launch tests in Cogniview
- **Results Submission**: Send comprehensive test results back to AIO

---

## Base URL Configuration

### Current Deployment (Render)
```
https://trajectorie.onrender.com
```

### Future Deployment (GoDaddy)
```
https://your-domain.com
```

**Migration:** Only base URL changes. All endpoints remain the same.

---

## Authentication

### JWT Token Authentication

Both systems use **JSON Web Tokens (JWT)** with a shared secret.

**Environment Variable (both systems):**
```bash
AIO_INTEGRATION_SECRET=your-shared-secret-key
```

**Token Generation (AIO):**
```python
import jwt
from datetime import datetime, timedelta

token = jwt.encode({
    'user_id': 'EMP_789',
    'test_id': 'test-uuid',
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(minutes=15)
}, AIO_INTEGRATION_SECRET, algorithm='HS256')
```

**Token Validation (Cogniview):**
```python
import jwt

try:
    payload = jwt.decode(token, AIO_INTEGRATION_SECRET, algorithms=['HS256'])
    user_id = payload['user_id']
    test_id = payload['test_id']
except jwt.ExpiredSignatureError:
    # Token expired
except jwt.InvalidTokenError:
    # Invalid token
```

---

## Integration Flow

```
┌─────────────────────────────────────────────────────────┐
│                  COMPLETE INTEGRATION FLOW               │
└─────────────────────────────────────────────────────────┘

STEP 1: TEST METADATA SYNC
   Admin creates test in Cogniview
          ↓
   Cogniview → POST /api/receive-test-metadata → AIO
          ↓
   AIO stores test config and shows to users

STEP 2: TEST LAUNCH  
   User clicks "Attempt Test" in AIO
          ↓
   AIO generates JWT token
          ↓
   AIO → POST /api/integration/test-launch → Cogniview
          ↓
   Cogniview validates token, creates session
          ↓
   Returns redirect_url to AIO
          ↓
   AIO redirects user via POST form
          ↓
   User lands on Cogniview test (instructions → quiz)

STEP 3: RESULTS SUBMISSION
   User completes test in Cogniview
          ↓
   Cogniview stores results in database
          ↓
   Cogniview → POST /api/receive-test-results → AIO
          ↓
   User redirects back to AIO dashboard
```

---

## Handshake 1: Test Metadata Sync

**Direction:** Cogniview → AIO  
**Trigger:** Automatically when admin creates test in Cogniview  
**Note:** Cogniview sends this data automatically. No manual action required.

### Endpoint (AIO must implement)
```
POST {AIO_BASE_URL}/api/receive-test-metadata
```

### Request Headers
```
Content-Type: application/json
```

### Request Body
See `schemas/test_metadata_sync.json` for complete schema.

Example:
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

### Success Response (HTTP 200)
```json
{
  "success": true,
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "message": "Test metadata received successfully"
}
```

### Error Responses
- **400 Bad Request:** Invalid data format or missing required fields

See `schemas/error_responses.json` → `metadata_sync_errors` for details

---

## Handshake 2: Test Launch

**Direction:** AIO → Cogniview → User  
**Trigger:** User clicks "Attempt Test" in AIO

### Step 1: AIO Sends Launch Request

**Endpoint (Cogniview will implement):**
```
POST {COGNIVIEW_BASE_URL}/api/integration/test-launch
```

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
See `schemas/test_launch_request.json` for complete schema.

Example:
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

**Success Response from Cogniview (HTTP 200):**
```json
{
  "success": true,
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "redirect_url": "https://trajectorie.onrender.com/load_quiz",
  "message": "User authenticated successfully"
}
```

**Error Responses:**
- **401 Unauthorized:** Invalid/expired auth_token
- **404 Not Found:** Test not found
- **400 Bad Request:** Missing required fields

See `schemas/test_launch_errors.json` for complete error details

### Step 2: AIO Redirects User

After receiving success response, AIO must redirect user via **POST form**:

```html
<form method="POST" action="https://trajectorie.onrender.com/load_quiz" id="launchForm">
  <input type="hidden" name="test_name" value="06fc6856-dc27-4756-a296-bca09272701c">
</form>
<script>
  document.getElementById('launchForm').submit();
</script>
```

**Important:** 
- Must use POST (not GET)
- Form field name: `test_name`
- Form value: `test_id` from request

### Step 3: User Experience

1. User lands on Cogniview test page
2. Instructions screen shows automatically
3. User clicks "Start Test"
4. Quiz loads with questions
5. After completion, user redirects to `return_url`

---

## Handshake 3: Results Submission

**Direction:** Cogniview → AIO  
**Trigger:** User submits test in Cogniview

### Endpoint (AIO must implement)
```
POST {AIO_BASE_URL}/api/receive-test-results
```

### Request Headers
```
Content-Type: application/json
```

### Request Body
See `schemas/test_results_submission.json` for complete schema.

Example:
```json
{
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "completion_status": "COMPLETED",
  "total_score_obtained": 40,
  "detailed_response": [...]
}
```

### Success Response from AIO (HTTP 200)
```json
{
  "success": true,
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "message": "Results received successfully"
}
```

### Error Responses
- **400 Bad Request:** Invalid data format or missing required fields

See `schemas/error_responses.json` → `results_submission_errors` for details

---

## Error Handling

All errors follow this format:

```json
{
  "success": false,
  "detail": "Human-readable error message"
}
```

### Common Errors

**Test Not Found (404)**
```json
{
  "success": false,
  "detail": "Test not found: 06fc6856-dc27-4756-a296-bca09272701c"
}
```

**Invalid Token (401)**
```json
{
  "success": false,
  "detail": "Authentication token is invalid or expired"
}
```

**Missing Fields (400)**
```json
{
  "success": false,
  "detail": "Missing required fields: user_id, test_id, auth_token"
}
```

See `schemas/error_responses.json` for complete list.

**End of API Documentation**
