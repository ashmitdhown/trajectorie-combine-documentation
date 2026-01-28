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

# Get Firebase client
db = firestore.client()

# Get integration secret from environment
INTEGRATION_SECRET = os.environ.get('INTEGRATION_SECRET', '')


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
            # Decode and validate JWT token
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
        test_query = db.collection('created_tests').where('test_id', '==', test_id).limit(1).stream()
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
        
        # Send to external system
        endpoint = f"{external_base_url}/api/receive-test-results"
        
        response = requests.post(
            endpoint,
            json=payload,
            headers={'Content-Type': 'application/json'},
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
