"""
External Integration Routes (AIO/Third-party Systems)
Handles test launch from external systems with JWT authentication.
This is completely isolated from existing Cogniview functionality.
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
import jwt
import os
from firebase_admin import firestore
from datetime import datetime

# Create blueprint for external integration
external_bp = Blueprint('external_integration', __name__)

# Lazy initialization for Firebase client (avoid import-time initialization)
_db = None

def get_db():
    """Get Firestore client with lazy initialization."""
    global _db
    if _db is None:
        _db = firestore.client()
    return _db

# Get configuration from environment
INTEGRATION_SECRET = os.environ.get('INTEGRATION_SECRET', '') # This is the KEY used to verify JWTs
EXTERNAL_AUTH_TOKEN = os.environ.get('EXTERNAL_AUTH_TOKEN', '') # This is the actual Token for the Bearer header


@external_bp.route('/api/integration/test-launch', methods=['POST'])
def test_launch():
    """
    Handle test launch from external system (e.g., AIO).
    
    Request Body:
        - user_id: External system user ID
        - user_name: Username/login ID
        - first_name: User's first name
        - last_name: User's last name
        - test_id: Test identifier
        - auth_token: JWT token for authentication
        - return_url: URL to redirect user after test completion
    
    Returns:
        Success: {"success": true, "redirect_url": "...", "message": "..."}
        Error: {"success": false, "detail": "error message"}
    """
    
    try:
        data = request.get_json()
        
        # Extract required fields
        user_id = data.get('user_id')
        user_name = data.get('user_name')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        test_id = data.get('test_id')
        auth_token = data.get('auth_token')
        return_url = data.get('return_url')
        
        # Validate all required fields are present
        required_fields = ['user_id', 'user_name', 'first_name', 'last_name', 
                          'test_id', 'auth_token', 'return_url']
        missing_fields = [f for f in required_fields if not data.get(f)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'detail': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # ═════════════════════════════════════════════════════════
        #                   JWT TOKEN VALIDATION
        # ═════════════════════════════════════════════════════════
        
        try:
            # Decode and validate JWT token using the INTEGRATION_SECRET (the key)
            payload = jwt.decode(
                auth_token,
                INTEGRATION_SECRET,
                algorithms=['HS256']
            )
            
            # Verify token matches request data
            if payload.get('user_id') != user_id:
                return jsonify({
                    'success': False,
                    'detail': 'Token user_id does not match request'
                }), 401
            
            if payload.get('test_id') != test_id:
                return jsonify({
                    'success': False,
                    'detail': 'Token test_id does not match request'
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'detail': 'Authentication token has expired'
            }), 401
            
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'detail': 'Authentication token is invalid'
            }), 401
        
        # ═════════════════════════════════════════════════════════
        #                   VERIFY TEST EXISTS
        # ═════════════════════════════════════════════════════════
        
        # Check if test exists in created_tests collection
        test_query = get_db().collection('created_tests').where('test_id', '==', test_id).limit(1).stream()
        test_dict = None
        
        for doc in test_query:
            test_dict = doc.to_dict()
            break
        
        if not test_dict:
            return jsonify({
                'success': False,
                'detail': f'Test not found: {test_id}'
            }), 404
        
        # ═════════════════════════════════════════════════════════
        #                   CREATE SESSION
        # ═════════════════════════════════════════════════════════
        
        # Create session with user data from external system
        session['user_data'] = {
            'user_id': user_id,
            'login_id': user_name,
            'username': user_name,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': True
        }
        
        # Set top-level session fields for login_required decorator compatibility
        session['user_id'] = user_id
        session['user_login_id'] = user_name
        
        # Mark this as an integration session
        session['integration_mode'] = True
        session['return_url'] = return_url
        session['external_test_id'] = test_id
        
        # ═════════════════════════════════════════════════════════
        #                   SUCCESS RESPONSE
        # ═════════════════════════════════════════════════════════
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'test_id': test_id,
            'redirect_url': url_for('load_quiz', _external=True),
            'message': 'User authenticated successfully'
        }), 200
        
    except Exception as e:
        # Log error for debugging
        print(f"Error in test_launch: {str(e)}")
        
        return jsonify({
            'success': False,
            'detail': 'Internal server error'
        }), 500


def send_results_to_external_system(user_id, test_id, results_data):
    """
    Send test results to external system (e.g., AIO).
    
    Args:
        user_id: User identifier from external system
        test_id: Test identifier
        results_data: Dictionary containing test results
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    import requests
    
    try:
        # Get external system base URL from environment
        external_base_url = os.environ.get('EXTERNAL_BASE_URL', '')
        
        if not external_base_url:
            print("EXTERNAL_BASE_URL not configured")
            return False
        
        # Prepare results payload
        payload = {
            'user_id': user_id,
            'test_id': test_id,
            'completion_status': results_data.get('completion_status', 'COMPLETED'),
            'total_score_obtained': results_data.get('total_score_obtained', 0),
            'detailed_response': results_data.get('detailed_response', [])
        }
        
        # Prepare headers with Authorization using the static Bearer token
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {EXTERNAL_AUTH_TOKEN}"
        }
        
        # Send to external system
        endpoint = f"{external_base_url}/api/TestSystem/SubmitCogniviewResult"
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"Results sent successfully to external system for user {user_id}")
            return True
        else:
            print(f"Failed to send results: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error sending results to external system: {str(e)}")
        return False


@external_bp.route('/api/integration/sync-test/<test_id>', methods=['POST'])
def trigger_test_sync(test_id):
    """
    Manually trigger a sync for a specific test metadata to AIO.
    This allows AIO to pull or Cogniview to push metadata for a specific test.
    """
    auth_token = request.headers.get('Authorization')
    if not auth_token or auth_token != f"Bearer {INTEGRATION_SECRET}":
        return jsonify({'success': False, 'detail': 'Unauthorized'}), 401
        
    # Run in background to not block
    import threading
    thread = threading.Thread(target=sync_test_metadata_to_external, args=(test_id,))
    thread.start()
    
    return jsonify({'success': True, 'message': f'Sync triggered for test {test_id}'})


def sync_test_metadata_to_external(test_id):
    """
    Push test metadata to external system (Handshake 1).
    Collects test info, competency hierarchy, and full question details.
    """
    import requests
    from ..controllers.admin_controller import get_question_from_question_id
    
    try:
        external_base_url = os.environ.get('EXTERNAL_BASE_URL', '')
        if not external_base_url:
            print("EXTERNAL_BASE_URL not configured for sync")
            return False

        # 1. Fetch test details
        test_query = get_db().collection('created_tests').where('test_id', '==', test_id).limit(1).stream()
        test_data = None
        for doc in test_query:
            test_data = doc.to_dict()
            break
            
        if not test_data:
            print(f"Sync error: Test {test_id} not found")
            return False

        # 2. Collect Questions and Competencies
        questions_list = []
        competencies_map = {}
        
        question_ids = test_data.get('Questions', [])
        for qid in question_ids:
            q = get_question_from_question_id(qid)
            if not q:
                continue
                
            q_type = q.get('q_type', '')
            # Try to get max marks from question or estimate
            # Note: Using a simplified marks check for sync metadata
            max_score = q.get('marks') or q.get('max_marks') or 1 
            
            comp_id = q.get('competencyId') or q.get('competency', 'GENERAL')
            comp_name = q.get('competencyName') or q.get('competency', 'General')
            sub_comp_id = q.get('subCompetencyId') or q.get('subcompetency', 'GENERAL_SUB')
            sub_comp_name = q.get('subCompetencyName') or q.get('subcompetency', 'General Sub')

            # Build questions payload
            questions_list.append({
                "question_id": str(qid),
                "question_text": q.get('question_text') or q.get('question', ''),
                "competency_id": comp_id,
                "competency_name": comp_name,
                "sub_competency_id": sub_comp_id,
                "sub_competency_name": sub_comp_name,
                "max_score": max_score,
                "time_alloted_seconds": int(q.get('time_alloted') or q.get('time_allotted') or 60),
                "question_type": q_type
            })

            # Track for competency hierarchy
            if comp_id not in competencies_map:
                competencies_map[comp_id] = {
                    "competency_id": comp_id,
                    "competency_name": comp_name,
                    "sub_competencies": {}
                }
            
            if sub_comp_id not in competencies_map[comp_id]["sub_competencies"]:
                competencies_map[comp_id]["sub_competencies"][sub_comp_id] = {
                    "sub_competency_id": sub_comp_id,
                    "sub_competency_name": sub_comp_name,
                    "max_score_for_sub_competency": 0
                }
            
            competencies_map[comp_id]["sub_competencies"][sub_comp_id]["max_score_for_sub_competency"] += max_score

        # 3. Format Competencies array
        formatted_competencies = []
        for c_id, c_data in competencies_map.items():
            subs = list(c_data["sub_competencies"].values())
            formatted_competencies.append({
                "competency_id": c_id,
                "competency_name": c_data["competency_name"],
                "sub_competencies": subs
            })

        # 4. Final Payload
        payload = {
            "test_id": test_id,
            "test_name": test_data.get('Test Name', ''),
            "duration_min": int(test_data.get('Test Duration (min)', 30)),
            "number_of_questions": len(questions_list),
            "mode": test_data.get('Test Type', 'assessment').lower(),
            "total_marks": test_data.get('Total_Marks', 0),
            "competencies": formatted_competencies,
            "questions": questions_list
        }

        # 5. Push to AIO with Authorization using the static Bearer token
        endpoint = f"{external_base_url}/api/TestSystem/CreateCogniviewTest"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {EXTERNAL_AUTH_TOKEN}"
        }
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            print(f"✓ Metadata sync successful for test {test_id}")
            return True
        else:
            print(f"✗ Metadata sync failed: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"Error during metadata sync: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

