"""
CASS - Utility Decorators
Common decorators for API routes and functions
"""
from functools import wraps
from flask import jsonify, request
from flask_login import current_user
import time
import logging

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin access for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def camera_access_required(f):
    """Decorator to check camera access permission"""
    @wraps(f)
    def decorated_function(camera_id, *args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not current_user.is_admin and not current_user.has_camera_access(camera_id):
            return jsonify({'error': 'Access denied to this camera'}), 403
        
        return f(camera_id, *args, **kwargs)
    return decorated_function


def validate_json(*required_fields):
    """Decorator to validate JSON request body contains required fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing': missing_fields
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def handle_errors(f):
    """Decorator to handle exceptions and return proper error responses"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Invalid input', 'details': str(e)}), 400
        except PermissionError as e:
            logger.error(f"Permission error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Permission denied', 'details': str(e)}), 403
        except FileNotFoundError as e:
            logger.error(f"Not found error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Resource not found', 'details': str(e)}), 404
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    return decorated_function


def log_performance(threshold_ms=1000):
    """Decorator to log slow operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if elapsed_ms > threshold_ms:
                logger.warning(
                    f"Slow operation: {f.__name__} took {elapsed_ms:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )
            
            return result
        return decorated_function
    return decorator


def cache_response(timeout=300):
    """
    Decorator to cache function responses
    Note: This is a simple in-memory cache. For production, use Flask-Caching
    """
    cache = {}
    cache_times = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            current_time = time.time()
            
            # Check if cached result exists and is not expired
            if cache_key in cache and cache_key in cache_times:
                if current_time - cache_times[cache_key] < timeout:
                    logger.debug(f"Cache hit for {f.__name__}")
                    return cache[cache_key]
            
            # Call function and cache result
            result = f(*args, **kwargs)
            cache[cache_key] = result
            cache_times[cache_key] = current_time
            
            # Simple cache cleanup: remove oldest entries if cache is too large
            if len(cache) > 1000:
                oldest_key = min(cache_times, key=cache_times.get)
                del cache[oldest_key]
                del cache_times[oldest_key]
            
            return result
        
        return decorated_function
    return decorator
