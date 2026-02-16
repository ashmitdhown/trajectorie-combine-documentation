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

Both systems use **JSON Web Tokens (JWT)** and static Bearer tokens.

**Environment Variables (Cogniview):**
```bash
# Security Key for JWT validation (AIO -> Cogniview)
INTEGRATION_SECRET=your-shared-secret-key

# Static Token for Bearer Authorization (Cogniview -> AIO)
EXTERNAL_AUTH_TOKEN=your-matching-bearer-token
```

**JWT Payload Format (AIO must include):**
```json
{
  "user_id": "EMP_789",
  "test_id": "06fc6856-dc27-4756-a296-bca09272701c",
  "iat": 1737964638,
  "exp": 1737965538
}
```

**Required Fields:**
- `user_id`: User identifier from AIO system
- `test_id`: Test identifier
- `iat`: Issued at timestamp (current time)
- `exp`: Expiration timestamp (iat + 15 minutes)

**Token Expiry:** 15 minutes

**Algorithm:** HS256

---

## Integration Flow

```
┌─────────────────────────────────────────────────────────┐
│                  COMPLETE INTEGRATION FLOW               │
└─────────────────────────────────────────────────────────┘

STEP 1: TEST METADATA SYNC
   Admin creates test in Cogniview
          ↓
   Cogniview → POST /api/TestSystem/CreateCogniviewTest → AIO
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
   AIO redirects user to Cogniview
          ↓
   User lands on Cogniview test (instructions → quiz)

STEP 3: RESULTS SUBMISSION
   User completes test in Cogniview
          ↓
   Cogniview stores results in database
          ↓
   Cogniview → POST /api/TestSystem/SubmitCogniviewResult → AIO
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
POST {AIO_BASE_URL}/api/TestSystem/CreateCogniviewTest
```

### Request Headers
```
Content-Type: application/json
Authorization: Bearer {EXTERNAL_AUTH_TOKEN}
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

After receiving success, AIO redirects user to `redirect_url` returned by Cogniview.

**Redirect Details:**
- URL: Use `redirect_url` from success response
- Method: POST
- Parameter: `test_name` with value = `test_id`

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
POST {AIO_BASE_URL}/api/TestSystem/SubmitCogniviewResult
```

### Request Headers
```
Content-Type: application/json
Authorization: Bearer {EXTERNAL_AUTH_TOKEN}
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

### Post-Submission: User Redirect

After successfully sending results to AIO, Cogniview must redirect user to the `return_url` provided in the initial test launch request (Handshake 2).

**Example:**
```python
# After sending results to AIO
return_url = session.get('return_url', 'https://aio-system.com/dashboard')
return redirect(return_url)
```

User returns to AIO dashboard where they can see their test completion status.

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
