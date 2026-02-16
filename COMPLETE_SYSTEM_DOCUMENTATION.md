# Trajectorie - Complete System Documentation

**Document Version:** 1.0  
**Last Updated:** February 5, 2026  
**Current Deployment:** Render (To be migrated to custom domain in future)

---

## Table of Contents

1. [Overall Architecture](#1-overall-architecture)
2. [Current Infrastructure Details](#2-current-infrastructure-details)
3. [Configuration Details](#3-configuration-details)
4. [URLs and Credentials](#4-urls-and-credentials)
5. [Git Repository and Setup](#5-git-repository-and-setup)
6. [API Keys and Secrets](#6-api-keys-and-secrets)
7. [Path of Logs](#7-path-of-logs)
8. [Test Scenarios and Results](#8-test-scenarios-and-results)
9. [Known Issues and Resolution Steps](#9-known-issues-and-resolution-steps)
10. [Deployment Details](#10-deployment-details)
11. [External Integration Documentation](#11-external-integration-documentation)
12. [Document Maintenance](#12-document-maintenance)

---

## 1. Overall Architecture

### 1.1 System Architecture Diagram

```
┌────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                            │
├────────────────────────────────────────────────────────────┤
│  • User Browser    • Admin Browser    • AIO System         │
└──────────────────────┬─────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              APPLICATION LAYER (Flask)                      │
├─────────────────────────────────────────────────────────────┤
│  Routes          Controllers       Services        Utils    │
│  • Questions     • Admin          • Scoring        • Drive  │
│  • Tests         • User           • Test Submit    • Session│
│  • Competency                     • External Int.           │
│  • Users                          • Drive Proxy             │
│  • Integration                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│                   DATA LAYER                               │
├────────────────────────────────────────────────────────────┤
│  Firebase Firestore            Google Drive (Images)       │
│  • QuestionandAnswers          • Question images           │
│  • competencies                • User uploads              │
│  • sub_competencies                                        │
│  • Users                                                   │
│  • user_data                                               │
│  • admin_data                                              │
│  • super_admin                                             │
│  • participants_data                                       │
│  • created_tests                                           │
│  • assigned_tests                                          │
│  • attempted_tests                                         │
│  • attempted_tests_from_q3                                 │
│  • question_data (legacy)                                  │
└────────────────────────────────────────────────────────────┘
```

### 1.2 Application Flows

**User Flow:**
```
Login → User Panel → View Tests → Start Quiz → Submit → View Results
```

**Admin Flow:**
```
Login → Admin Panel → Create Questions → Create Test → Assign to Users → View Results
```

**External Integration (AIO):**
```
AIO Launch → JWT Auth → User Test Session → Submit → Results to AIO → Return to AIO
```

---

## 2. Current Infrastructure Details

### 2.1 Database - Firebase Firestore

**Project:** `trajectorie-f93b8`  
**Type:** Cloud Firestore (NoSQL)

#### Database Collections:

```
Firestore
│
├── QuestionandAnswers/
│   ├── text_answer_short_answer/
│   │   └── questions/{question_id}
│   ├── text_answer_long_answer/
│   │   └── questions/{question_id}
│   ├── multiple_single_choice/
│   │   └── questions/{question_id}
│   ├── true_false/
│   │   └── questions/{question_id}
│   ├── fill_in_the_blanks/
│   │   └── questions/{question_id}
│   ├── spot_error_in_the_sentence/
│   │   └── questions/{question_id}
│   ├── match_the_column/
│   │   └── questions/{question_id}
│   ├── sequence_the_item_drag_and_drop_text/
│   │   └── questions/{question_id}
│   ├── sequence_the_item_drag_and_drop_image/
│   │   └── questions/{question_id}
│   ├── spot_the_object/
│   │   └── questions/{question_id}
│   ├── spot_the_difference/
│   │   └── questions/{question_id}
│   └── pattern_recognition/
│       └── questions/{question_id}
│
├── Users/
│   └── user{N}
│       ├── user_id
│       ├── first_name
│       ├── last_name
│       ├── gender
│       ├── email
│       ├── mobile_number
│       ├── login_id
│       ├── password
│       ├── supervisor_name
│       ├── supervisor_email
│       ├── created_at
│       └── created_by
│
├── admin_data/
│   └── {admin_username}
│       ├── username
│       ├── password
│       └── students (array of login_ids)
│
├── assigned_tests/
│   └── {assignment_id}
│       ├── test_id (UUID)
│       ├── test_name
│       ├── created_test_doc_id
│       ├── status (Active/Draft)
│       ├── participants (array)
│       ├── created_at
│       └── updated_at
│
├── attempted_tests/
│   └── {user_login_id}/
│       └── attempts/{attempt_id}
│           ├── test_id
│           ├── test_name
│           ├── total_score
│           ├── total_max_marks
│           ├── percentage
│           ├── completed_at
│           ├── test_response (object)
│           └── api_response (array)
│
├── attempted_tests_from_q3/
│   └── {user_login_id}/
│       └── attempts/{attempt_id}
│           ├── test_id
│           ├── test_name
│           ├── total_score
│           ├── total_max_marks
│           ├── percentage
│           ├── completed_at
│           ├── completion_status
│           ├── test_response (object)
│           └── detailed_response (array)
│
├── competencies/
│   └── {competency_id}
│       ├── competencyName
│       └── isActive
│
├── created_tests/
│   └── {test_doc_id}
│       ├── test_id (UUID)
│       ├── Test Name
│       ├── Test Type
│       ├── Test Duration (min)
│       ├── Best Test Time (min)
│       ├── Time Till Hint (sec)
│       ├── Questions (array of question IDs)
│       ├── total_marks
│       ├── status (Active/Draft)
│       ├── assigned_to (array)
│       ├── competency_id
│       ├── competency_name
│       ├── sub_competencies (array)
│       ├── created_at
│       └── created_by
│
├── participants_data/
│   └── {login_id}
│       ├── login_id
│       ├── password
│       ├── first_name
│       ├── last_name
│       ├── gender
│       ├── email
│       ├── mobile_number
│       ├── supervisor_name
│       ├── supervisor_email
│       └── tests_completed (array)
│
├── question_data/
│   └── {question_id}
│       ├── (Legacy question storage)
│       └── Various question type fields
│
├── sub_competencies/
│   └── {sub_competency_id}
│       ├── subCompetencyName
│       ├── competencyId
│       └── isActive
│
├── super_admin/
│   └── {superadmin_doc_id}
│       ├── username
│       └── password
│
└── user_data/
    └── user{N}
        ├── user_id
        ├── username
        ├── password
        ├── email
        ├── first_name
        ├── last_name
        ├── login_id
        ├── is_active
        └── created_at
```

### 2.2 Image Storage - Google Drive

**Method:** Google Drive API via Proxy Service  
**Proxy URL:** Apps Script deployed as web app

Images for questions are stored on Google Drive and accessed via a proxy service that converts Drive URLs to direct viewable URLs using `lh3.googleusercontent.com`.

### 2.3 API Server

**Framework:** Flask 2.2.3  
**Language:** Python 3.x  
**Web Server:** Gunicorn 20.1.0  
**Session:** Flask-Session (filesystem)

**Key Dependencies:**
- `firebase-admin==6.1.0`
- `google-cloud-firestore==2.9.1`
- `flask-cors==3.0.10`
- `PyJWT==2.9.0`
- `requests==2.32.3`

### 2.4 Authentication

**User/Admin:** Session-based (Flask sessions)  
**External (AIO):** JWT tokens (HS256, 15 min expiry)

---

## 3. Configuration Details

### 3.1 Question Types (12 Total)

1. `text_answer_short_answer` (tasa)
2. `text_answer_long_answer` (tala)
3. `multiple_single_choice` (mrq)
4. `true_false` (tf)
5. `fill_in_the_blanks` (tafib)
6. `spot_error_in_the_sentence` (ses)
7. `match_the_column` (mtc)
8. `sequence_the_item_drag_and_drop_text` (ts)
9. `sequence_the_item_drag_and_drop_image` (dad)
10. `spot_the_object` (sto)
11. `spot_the_difference` (std)
12. `pattern_recognition` (pr)

### 3.2 Environment Variables

**`.env.integration` file:**
```
INTEGRATION_SECRET=qYx9f4K8mZ2V7cW6e1D0B3TQJvLkH5pA0N6M4RrS8E=
EXTERNAL_AUTH_TOKEN=your-static-bearer-token
EXTERNAL_BASE_URL=https://digital.trajectorie.com/TrajectorieAllinOne_UAT
```

---

## 4. URLs and Credentials

### 4.1 Application URLs

**Production (Current):**
```
https://trajectorie.onrender.com
```

### 4.2 Firebase Console

**Firebase Project Console:**
```
https://console.firebase.google.com/project/trajectorie-f93b8
```
### 4.3 Key API Endpoints

#### Public:
- `GET /` - Home page
- `GET/POST /user/login` - User login
- `GET/POST /admin/login` - Admin login

#### User (Login Required):
- `GET /user/panel` - User dashboard
- `POST /load_quiz` - Load quiz
- `POST /submit_test` - Submit test
- `GET /user/get_assigned_tests` - Get assigned tests
- `GET /user/get_results` - Get results

#### Admin (Admin Login Required):
- `GET /admin/panel` - Admin dashboard
- `GET /admin/test-dashboard` - Test dashboard
- `POST /api/admin/create-test` - Create test
- `POST /api/admin/assign-test` - Assign test
- `GET /api/questions` - Get questions
- `POST /api/add-question` - Add question
- `GET /api/competencies` - Get competencies

#### External Integration:
- `POST /api/integration/test-launch` - Test launch from AIO (JWT required)

#### AIO Endpoints (To be implemented by AIO team):
- `POST {AIO_URL}/api/TestSystem/CreateCogniviewTest` - Receive test metadata
- `POST {AIO_URL}/api/TestSystem/SubmitCogniviewResult` - Receive results

---

## 5. Git Repository and Setup

### 5.1 Repository

**GitHub URL:**
```
https://github.com/ashmitdhown/trajectorie.git
```

**Branch:** `main`

### 5.2 Setup Instructions

**Clone Repository:**
```bash
git clone https://github.com/ashmitdhown/trajectorie.git
cd trajectorie
```

**Create Virtual Environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
```

**Add Firebase Credentials:**
Create `config/firebase_credentials.json` with your Firebase service account key.

**Run Application:**
```bash
python app.py
```

Or using Gunicorn:
```bash
gunicorn app:app
```

---

## 6. API Keys and Secrets

### 6.1 Firebase Credentials

**File:** `config/firebase_credentials.json`  
**Note:** Must be manually placed (gitignored)

**Firebase Console Access:**
```
Email: combine@trajectorie.com
Password: trajectorie@01
```

**Variable:** `INTEGRATION_SECRET`, `EXTERNAL_AUTH_TOKEN`  
**Value:** See `.env.integration`

`INTEGRATION_SECRET` is used for JWT validation (AIO → Cogniview).  
`EXTERNAL_AUTH_TOKEN` is used for Bearer authorization (Cogniview → AIO).

### 6.3 Flask Session Secret

```python
app.config['SECRET_KEY'] = 'your-secret-key-here'
```

---

## 7. Path of Logs

### 7.1 Application Logs

**Production (Render):**
- View in Render Dashboard → Logs tab
- URL: `https://dashboard.render.com/`

**Local Development:**
- Console output (stdout/stderr)

### 7.2 Session Data

**Path:** `/flask_session/`  
**Type:** Binary session files

### 7.3 Firebase Monitoring

**Firebase Console:**
```
https://console.firebase.google.com/project/trajectorie-f93b8/usage
```

Monitors:
- Firestore read/write operations
- Database usage

### 7.4 Debug Log Patterns

Key debug markers in code:
- `[DEBUG]` - Debug information
- `[ERROR]` - Error messages
- `[IMAGE TRANSFORM]` - Image URL transformations
- `[EXTERNAL INTEGRATION]` - External API calls

---

## 8. Test Scenarios and Results

### 8.1 Test Coverage
**Total Tests:** 18 scenarios (9 question types × 2 scenarios each)

### 8.2 Question Type Test Results

| Question Type | Test Scenarios | Status |
|--------------|----------------|---------|
| MCQ | Correct + Wrong answer | ✅ PASSED |
| True/False | All correct + Partial | ✅ PASSED |
| Fill in Blanks | All correct + Partial | ✅ PASSED |
| Match Column | All correct + Partial | ✅ PASSED |
| Spot Object | All found + Partial | ✅ PASSED |
| Drag & Drop | Correct + Partial sequence | ✅ PASSED |
| Short Answer | Exact + Keyword match | ✅ PASSED |
| Pattern Recognition | Correct pattern | ✅ PASSED |
| Spot Error | Error identified | ✅ PASSED |

### 8.3 Scoring Features Verified

✅ Correct answer detection  
✅ Partial credit calculation  
✅ Case-insensitive matching  
✅ Coordinate tolerance (±40px for hotspots)  
✅ Sequence validation  
✅ Substring matching  

### 8.4 Integration Tests

**AIO Integration:**
- ✅ JWT token generation
- ✅ JWT validation
- ✅ Test metadata sync
- ✅ Test launch flow
- ✅ Results submission

**User Flow:**
- ✅ Login → View tests → Take test → Submit → View results

**Admin Flow:**
- ✅ Login → Create questions → Create test → Assign → View results

---

## 9. Known Issues and Resolution Steps

### 9.1 Firebase Initialization Order (FIXED)

**Issue:** `ValueError: The default Firebase app does not exist`

**Cause:** `external_integration.py` accessed Firestore before initialization

**Fix:** Moved Firestore client access to function level, used dependency injection

```python
db = None

def init_db(firestore_client):
    global db
    db = firestore_client
```

---

### 9.2 Google Drive Rate Limiting (MITIGATED)

**Issue:** Rate limit errors when loading multiple Drive images

**Current Solution:**
- Drive Proxy Service implementation
- URL transformation to `lh3.googleusercontent.com`
- Caching and batch loading

```python
transformed_url = drive_proxy_service.get_presigned_url(drive_url)
```

---

### 9.3 Competency ID Management (FIXED)

**Issue:** No custom IDs for competencies/sub-competencies

**Fix:**
- Added custom ID input fields
- Auto-generate option
- Used IDs as Firestore document names
- Added bulk upload for sub-competencies via CSV

---

## 10. Deployment Details

### 10.1 Current Deployment - Render

**Platform:** Render.com  
**URL:** `https://trajectorie.onrender.com`  
**Auto-deploy:** From GitHub `main` branch

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
gunicorn app:app
```

### 10.2 Environment Setup on Render

Required environment variables:
- `AIO_INTEGRATION_SECRET`
- `EXTERNAL_BASE_URL`

Required files:
- `config/firebase_credentials.json` (upload manually)

### 10.3 Pre-Deployment Checklist

- [ ] All dependencies in `requirements.txt`
- [ ] Environment variables set
- [ ] Firebase credentials uploaded
- [ ] Database connection tested
- [ ] All test scenarios passed
- [ ] API endpoints verified

### 10.4 Future Migration

**Note:** Currently deployed on Render. Future migration to custom domain planned.

**Migration Steps:**
1. Configure new hosting environment
2. Update DNS settings
3. Deploy application
4. Update environment variables
5. Upload Firebase credentials
6. Update URL references in code
7. Notify AIO team of URL changes

**Important:** No code changes needed for URL migration, only configuration updates.

### 10.5 Backup and Recovery

**Database Backup:**
- Firebase automatic backups enabled
- Export via Firebase CLI:
  ```bash
  gcloud firestore export gs://[BUCKET_NAME]/backups
  ```

**Code Backup:**
- GitHub repository (primary)
- Version control via Git tags

### 10.6 Monitoring

**Key Metrics:**
- Firestore reads/writes (stay within free tier: 50K reads/day)
- Response time (target: < 2 seconds)
- Error rates (review logs)

**Regular Tasks:**
- Weekly: Review error logs
- Monthly: Check dependency updates
- Quarterly: Optimize database queries

## 11. External Integration Documentation

**Location:** `/integration_docs/`
**Github Link:** https://github.com/ashmitdhown/trajectorie-combine-documentation

For developers working on AIO or other external system integration, comprehensive documentation is available in the `integration_docs/` directory:

**Key Files:**
- **`README.md`** - Overview and quick start
- **`API_OVERVIEW.md`** - Complete API reference with full endpoint details
- **`AIO_IMPLEMENTATION_GUIDE.md`** - Step-by-step guide for AIO team implementation

**JSON Schemas** (`/schemas/` directory):
- `test_metadata_sync.json` - Test config sync from Cogniview to AIO
- `test_launch_request.json` - Launch request format from AIO
- `test_launch_success.json` - Success response format
- `test_launch_errors.json` - Error response examples
- `test_results_submission.json` - Results format to AIO
- `error_responses.json` - General error formats

**Integration Flow:**
1. **Test Metadata Sync:** Cogniview → AIO (after test creation)
2. **Test Launch:** AIO → Cogniview (JWT authentication)
3. **Results Submission:** Cogniview → AIO (after test completion)

**Base URL Requirements:**
- **Cogniview:** `https://trajectorie.onrender.com` (Target URL for AIO launch requests)
- **AIO:** `https://digital.trajectorie.com/TrajectorieAllinOne_UAT` (Example UAT URL)

---

## 12. Document Maintenance

**Owner:** System Administrator  
**Last Review:** February 5, 2026  
**Next Review:** May 5, 2026

**Repository:** https://github.com/ashmitdhown/trajectorie
**Repository:** https://github.com/ashmitdhown/trajectorie-combine-documentation

