"""
Route handler for test submission with proper scoring and competency aggregation.
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone
from functools import wraps
from firebase_admin import firestore
from ..services.test_completion_service import TestCompletionService

# Create blueprint
test_submission_bp = Blueprint('test_submission', __name__)

# Initialize Firestore (will be injected from main app)
db = None
test_completion_service = None

def init_db(database):
    global db, test_completion_service
    db = database
    test_completion_service = TestCompletionService(db)

# Decorator for user login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for either user_id or user_login_id in session
        if 'user_id' not in session and 'user_login_id' not in session:
            return jsonify({'error': 'Not logged in'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_question_from_question_id(question_id):
    """
    Fetch a question using the new Firestore structure or legacy.
    Copied from user_controller.py - should be centralized later.
    """
    if isinstance(question_id, dict):
        question_id = str(
            question_id.get("id")
            or question_id.get("question_id")
            or question_id.get("qid")
            or ""
        )
    else:
        question_id = str(question_id)
    if not question_id:
        return {}

    # Map Firestore doc keys to q_type
    qtype_map = {
        "multiple_single_choice": "mrq",
        "mcq": "mrq",
        "text_answer_short_answer": "tasa",
        "text_answer_long_answer": "tala",
        "true_false": "tf",
        "true_&_false": "tf",
        "fill_in_the_blanks": "tafib",
        "match_the_column": "mtc",
        "sequence_the_item_drag_and_drop_image": "dad",
        "sequence_the_item_drag_and_drop_text": "ts",
        "pattern_recognition": "pr",
        "spot_the_object": "sto",
        "spot_the_difference": "std",
        "spot_error_in_the_sentence": "ses",
    }

    # Try new structure first
    for question_type_key, q_type in qtype_map.items():
        doc_ref = (
            db.collection("QuestionandAnswers")
            .document(question_type_key)
            .collection("questions")
            .document(question_id)
        )
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict() or {}
            data["question_id"] = question_id
            data["q_type"] = data.get("q_type") or q_type
            
            # Normalize q_type for scoring
            if "q_type" in data:
                raw_type = data["q_type"]
                norm_type = str(raw_type).lower().replace(' ', '_')
                data["q_type"] = qtype_map.get(norm_type, qtype_map.get(raw_type, raw_type))

            # Normalize nested structures (like statements array in TF)
            if data.get("q_type") == "tf":
                if "statements" in data and isinstance(data["statements"], list):
                    for i, stmt in enumerate(data["statements"], 1):
                        if f"answer_{i}" not in data:
                            data[f"answer_{i}"] = stmt.get("answer", "")
                        if f"marks_{i}" not in data:
                            data[f"marks_{i}"] = stmt.get("marks", "1")
            return data

    # Fallback: legacy collection
    legacy_ref = db.collection("question_data").document(question_id)
    legacy_doc = legacy_ref.get()
    if legacy_doc.exists:
        data = legacy_doc.to_dict() or {}
        data["question_id"] = question_id
        
        # Normalize q_type for scoring engine
        if "q_type" in data:
            raw_type = data["q_type"]
            norm_type = str(raw_type).lower().replace(' ', '_')
            data["q_type"] = qtype_map.get(norm_type, qtype_map.get(raw_type, raw_type))
            
        # IMPORTANT: Normalize nested structures (like statements array in TF)
        # This MUST match the normalization in app.py
        if data.get("q_type") == "tf":
            if "statements" in data and isinstance(data["statements"], list):
                for i, stmt in enumerate(data["statements"], 1):
                    if f"answer_{i}" not in data:
                        data[f"answer_{i}"] = stmt.get("answer", "")
                    if f"marks_{i}" not in data:
                        data[f"marks_{i}"] = stmt.get("marks", "1")
                        
        return data

    return {}


@test_submission_bp.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    """
    Handle final test submission with proper scoring and competency aggregation.
    
    Expected payload:
    {
        "test_name": "Test Name",
        "user_answers": {
            "question_id_1": {attempted_answer},
            "question_id_2": {attempted_answer},
            ...
        },
        "time_tracking": {
            "question_id_1": 45,
            "question_id_2": 62,
            ...
        }
    }
    """
    try:
        print("=" * 60)
        print("SUBMIT_TEST ENDPOINT CALLED")
        print("=" * 60)
        
        data = request.get_json()
        print(f"Received data keys: {data.keys() if data else 'NO DATA'}")
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        test_name = data.get('test_name')
        user_answers = data.get('user_answers', {})
        time_tracking = data.get('time_tracking', {})
        
        print(f"Test name: {test_name}")
        print(f"User answers count: {len(user_answers)}")
        print(f"Time tracking count: {len(time_tracking)}")
        
        if not test_name:
            return jsonify({'error': 'Test name is required'}), 400
        
        user_login_id = session.get('user_login_id') or session.get('user_id')
        print(f"User ID: {user_login_id}")
        
        if not user_login_id:
            return jsonify({'error': 'User ID not found in session'}), 401
        
        # Get test data by test_id
        # First try to get test by test_id field
        test_data = None
        test_id = test_name  # Default to test_name
        
        # Query by test_id field
        print(f"Looking for test with test_id: {test_name}")
        created_tests_query = db.collection('created_tests').where('test_id', '==', test_name).limit(1).stream()
        for test_doc in created_tests_query:
            test_data = test_doc.to_dict()
            test_id = test_data.get('test_id', test_name)
            test_ref = test_doc.reference
            print(f"Found test by test_id query")
            break
        
        # Fallback: try test_name as document ID
        if not test_data:
            print(f"Trying test_name as document ID: {test_name}")
            test_ref = db.collection('created_tests').document(test_name)
            test_doc = test_ref.get()
            if test_doc.exists:
                test_data = test_doc.to_dict()
                test_id = test_data.get('test_id', test_name)
                print(f"Found test by document ID")
        
        if not test_data:
            print(f"ERROR: Test '{test_name}' not found")
            return jsonify({'error': 'Test not found'}), 404
        
        test_mode = test_data.get('Test Type', 'Assessment')
        
        print(f"Test ID: {test_id}")
        print(f"Test Mode: {test_mode}")
        print(f"Test Duration: {test_data.get('Test Duration (min)', 0)} min")
        
        # Check if test is active
        if test_data.get('status') != 'Active':
            print(f"ERROR: Test '{test_name}' is not active")
            return jsonify({'error': 'Test is not active'}), 403
        
        # Get all questions for this test
        question_ids = test_data.get('Questions', [])
        print(f"Question IDs in test: {question_ids}")
        
        questions = []
        
        for question_id in question_ids:
            question = get_question_from_question_id(question_id)
            if question:
                questions.append(question)
            else:
                # IMPORTANT: Keep a placeholder to preserve indexing (Q1, Q2, etc.)
                # If we skip this, Q2 would become 'q1' in the results, causing confusion.
                print(f"WARNING: Question {question_id} not found. Adding placeholder.")
                questions.append({
                    'question_id': question_id,
                    'q_type': 'missing',
                    'question_title': 'Missing Question (Deleted from Database)',
                    'is_missing': True,
                    'points': 0,
                    'marks': 0,
                    'score': 0
                })
        
        print(f"Questions processed: {len(questions)}")
        
        if not questions:
            return jsonify({'error': 'No questions found for this test'}), 400
        
        # Get test start time from session (or use current time as fallback)
        test_start_time = session.get('test_start_time')
        if test_start_time:
            if isinstance(test_start_time, str):
                test_start_time = datetime.fromisoformat(test_start_time)
        else:
            # Fallback: assume test started when first question was answered
            test_start_time = datetime.now(timezone.utc)
        
        print(f"Test start time: {test_start_time}")
        print(f"Calling test_completion_service.complete_test()...")
        
        # Complete the test using the service
        attempt_record = test_completion_service.complete_test(
            user_id=user_login_id,
            test_id=test_id,
            test_name=test_name,
            questions=questions,
            user_answers=user_answers,
            time_tracking=time_tracking,
            test_start_time=test_start_time,
            test_mode=test_mode
        )
        
        print(f"✓ Test completion service finished!")
        print(f"Total score: {attempt_record['total_score']}/{attempt_record['total_max_marks']}")
        
        # Remove test from user's assigned tests in created_tests
        test_ref.update({
            'assigned_to': firestore.ArrayRemove([user_login_id]),
            'Test_Participation': firestore.Increment(1)
        })

        # Update status in assigned_tests collection
        try:
            assigned_tests_query = db.collection('assigned_tests').where('created_test_doc_id', '==', test_ref.id).stream()
            for assigned_doc in assigned_tests_query:
                assigned_data = assigned_doc.to_dict()
                participants = assigned_data.get('participants', [])
                updated = False
                for p in participants:
                    if p.get('user_id') == user_login_id:
                        p['status'] = 'completed'
                        p['completed_at'] = attempt_record['completed_at']
                        updated = True
                if updated:
                    assigned_doc.reference.update({'participants': participants})
                    print(f"✓ Updated assigned_tests status to completed for {user_login_id}")
        except Exception as e:
            print(f"Warning: Could not update status in assigned_tests: {e}")
        
        # Add to user's completed tests (legacy format for compatibility)
        participants_ref = db.collection('participants_data').document(user_login_id)
        
        # Calculate actual time taken
        time_taken_td = attempt_record['completed_at'] - test_start_time
        time_taken_sec = int(time_taken_td.total_seconds())

        test_obj = {
            "test_name": test_name,
            "test_type": test_mode,
            "total_questions": attempt_record['total_questions'],
            "total_time_min": test_data.get('Test Duration (min)', 0),
            "best_time_min": test_data.get('Best Test Time (min)', 0),
            "score": attempt_record['total_score'],
            "total_marks": attempt_record['total_max_marks'],
            "percentage": attempt_record['percentage'],
            "completed_at": attempt_record['completed_at'],
            "time_taken_sec": time_taken_sec
        }
        
        # Use set with merge to create document if it doesn't exist
        try:
            participants_ref.set({
                "tests_completed": firestore.ArrayUnion([test_obj])
            }, merge=True)
            print(f"✓ Updated participants_data for {user_login_id}")
        except Exception as e:
            print(f"Warning: Could not update participants_data: {e}")
            # Continue anyway - the attempted_tests collection is the source of truth
        
        # Clear session data
        session.pop('current_status', None)
        session.pop('test_start_time', None)
        
        # ═════════════════════════════════════════════════════════
        #     EXTERNAL INTEGRATION - Send Results & Redirect
        # ═════════════════════════════════════════════════════════
        # Only executes for external system users (flag-based detection)
        
        if session.get('integration_mode'):
            try:
                from .external_integration import send_results_to_external_system
                
                # Transform internal api_response to external system format
                detailed_response = []
                
                for competency in attempt_record.get('api_response', []):
                    competency_obj = {
                        'competency_id': competency.get('competency_code', ''),
                        'competency_name': competency.get('competency_name', ''),
                        'sub_competencies': []
                    }
                    
                    for sub_comp in competency.get('sub_competencies', []):
                        # Build questions array with time tracking from test_response
                        questions_list = []
                        
                        # Get all questions for this sub-competency from test_response
                        for q_key, q_data in attempt_record.get('test_response', {}).items():
                            # Check if this question belongs to this sub-competency
                            question_id = q_data.get('question_id')
                            
                            # Find the original question to check competency/sub-competency
                            for orig_q in questions:
                                orig_q_id = str(orig_q.get('question_id') or orig_q.get('id', ''))
                                if orig_q_id == question_id:
                                    q_sub_comp_id = orig_q.get('subCompetencyId') or orig_q.get('subcompetency', '')
                                    if q_sub_comp_id == sub_comp.get('sub_competency_code'):
                                        questions_list.append({
                                            'question_id': question_id,
                                            'time_taken_sec': q_data.get('time_spent', 0)
                                        })
                                    break
                        
                        sub_comp_obj = {
                            'sub_competency_id': sub_comp.get('sub_competency_code', ''),
                            'sub_competency_name': sub_comp.get('sub_competency_name', ''),
                            'marks_obtained_sub_competency': sub_comp.get('marks_obtained_sub_competency', 0),
                            'time_taken_sec': sub_comp.get('time_taken', 0),
                            'questions': questions_list
                        }
                        
                        competency_obj['sub_competencies'].append(sub_comp_obj)
                    
                    detailed_response.append(competency_obj)
                
                # Prepare results in external system format
                external_results = {
                    'completion_status': 'COMPLETED',
                    'total_score_obtained': attempt_record['total_score'],
                    'detailed_response': detailed_response
                }
                
                # Send results to external system
                external_user_id = session.get('user_data', {}).get('user_id')
                external_test_id = session.get('external_test_id', test_id)
                
                send_results_to_external_system(
                    user_id=external_user_id,
                    test_id=external_test_id,
                    results_data=external_results
                )
                
                print(f"✓ Results sent to external system for user {external_user_id}")
                
                # ═════════════════════════════════════════════════════════
                #     STORE IN attempted_tests_from_q3 COLLECTION
                # ═════════════════════════════════════════════════════════
                # Store integration user attempts separately
                
                try:
                    attempt_id = f"{test_id}_{int(attempt_record['completed_at'].timestamp())}"
                    
                    # Use user_name (login_id) as document ID to match normal pattern
                    user_name = session.get('user_login_id') or external_user_id
                    
                    # Store in attempted_tests_from_q3/{user_name}/attempts/{attempt_id}
                    db.collection('attempted_tests_from_q3').document(user_name)\
                        .collection('attempts').document(attempt_id).set(attempt_record)
                    
                    print(f"✓ Stored integration attempt in attempted_tests_from_q3 for user {user_name}")
                    
                except Exception as storage_error:
                    print(f"Warning: Could not store in attempted_tests_from_q3: {storage_error}")
                    # Continue anyway - results already sent to external system
                
            except Exception as e:
                print(f"Warning: Could not send results to external system: {e}")
                import traceback
                traceback.print_exc()
                # Continue anyway - user submission was successful
        
        # ═════════════════════════════════════════════════════════
        
        return jsonify({
            'success': True,
            'message': 'Test submitted successfully',
            'attempt_id': f"{test_id}_{int(attempt_record['completed_at'].timestamp())}",
            'score': attempt_record['total_score'],
            'total_marks': attempt_record['total_max_marks'],
            'percentage': attempt_record['percentage'],
            'test_name': test_name,
            'redirect_url': session.get('return_url') if session.get('integration_mode') else None
        })
        
    except Exception as e:
        print(f"Error in submit_test: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'message': 'Internal server error'}), 500
