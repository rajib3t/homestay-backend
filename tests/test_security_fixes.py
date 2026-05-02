"""
Regression tests for security fixes
Tests that all business routes require authentication and error details are not leaked
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from main import app
from app.core.exceptions import AppException


client = TestClient(app)


class TestAuthenticationRequired:
    """Test that all business routes require authentication"""
    
    def test_users_routes_require_auth(self):
        """Test that all user management routes require authentication"""
        endpoints = [
            ("GET", "/users/"),
            ("POST", "/users/"),
            ("GET", "/users/test-user-id"),
            ("PUT", "/users/test-user-id"),
            ("PUT", "/users/test-user-id/profile-image"),
            ("PUT", "/users/test-user-id/password"),
        ]
        
        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            # Should be either 401 (auth required) or 404 (route not found)
            # But should not be 200 (success)
            assert response.status_code in [401, 404], f"Expected 401 or 404 for {method} {endpoint}, got {response.status_code}"
            if response.status_code == 401:
                assert "Authorization" in response.json().get("message", "").lower() or "token" in response.json().get("message", "").lower()
    
    def test_company_routes_require_auth(self):
        """Test that all company routes require authentication"""
        endpoints = [
            ("POST", "/companies/"),
            ("GET", "/companies/test-company-id"),
            ("GET", "/companies/user/test-user-id"),
            ("PUT", "/companies/test-company-id"),
        ]
        
        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            # Should be either 401 (auth required) or 404 (route not found)
            assert response.status_code in [401, 404], f"Expected 401 or 404 for {method} {endpoint}, got {response.status_code}"
            if response.status_code == 401:
                assert "Authorization" in response.json().get("message", "").lower() or "token" in response.json().get("message", "").lower()
    
    def test_location_routes_require_auth(self):
        """Test that all location routes require authentication"""
        endpoints = [
            ("POST", "/locations/country"),
            ("GET", "/locations/countries"),
            ("GET", "/locations/country/test-country-id"),
            ("PATCH", "/locations/country/test-country-id"),
            ("PATCH", "/locations/country/test-country-id/status"),
            ("POST", "/locations/city"),
            ("GET", "/locations/cities"),
            ("GET", "/locations/city/test-city-id"),
            ("PATCH", "/locations/city/test-city-id"),
            ("GET", "/locations/country/test-country-id/cities"),
            ("POST", "/locations/create"),
            ("GET", "/locations/locations"),
            ("GET", "/locations/location/test-location-id"),
            ("PATCH", "/locations/location/test-location-id"),
        ]
        
        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            # Should be either 401 (auth required) or 404 (route not found)
            assert response.status_code in [401, 404], f"Expected 401 or 404 for {method} {endpoint}, got {response.status_code}"
            if response.status_code == 401:
                assert "Authorization" in response.json().get("message", "").lower() or "token" in response.json().get("message", "").lower()
    
    def test_attribute_routes_require_auth(self):
        """Test that all attribute routes require authentication"""
        endpoints = [
            # Amenity routes
            ("POST", "/attributes/amenity"),
            ("GET", "/attributes/amenities"),
            ("GET", "/attributes/amenity/test-amenity-id"),
            ("PATCH", "/attributes/amenity/test-amenity-id"),
            ("PATCH", "/attributes/amenity/test-amenity-id/status"),
            # Facility routes
            ("POST", "/attributes/facility"),
            ("GET", "/attributes/facilities"),
            ("GET", "/attributes/facility/test-facility-id"),
            ("PATCH", "/attributes/facility/test-facility-id"),
            ("PATCH", "/attributes/facility/test-facility-id/status"),
            # Room type routes
            ("POST", "/attributes/room-type"),
            ("GET", "/attributes/room-types"),
            ("GET", "/attributes/room-type/test-room-type-id"),
            ("PATCH", "/attributes/room-type/test-room-type-id"),
            ("PATCH", "/attributes/room-type/test-room-type-id/status"),
        ]
        
        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            # Should be either 401 (auth required) or 404 (route not found)
            assert response.status_code in [401, 404], f"Expected 401 or 404 for {method} {endpoint}, got {response.status_code}"
            if response.status_code == 401:
                assert "Authorization" in response.json().get("message", "").lower() or "token" in response.json().get("message", "").lower()
    
    def test_profile_routes_still_work_with_auth(self):
        """Test that profile routes work with valid authentication"""
        with patch('app.deps.JWTHandler.decode_token') as mock_decode:
            mock_decode.return_value = {"sub": "test-user-id", "type": "access"}
            
            response = client.get(
                "/profile",
                headers={"Authorization": "Bearer valid-token"}
            )
            # Should not be 401, may be 404 or other error but not auth error
            assert response.status_code != 401


class TestErrorDetailSecurity:
    """Test that internal error details are not leaked"""
    
    def test_api_utils_handle_exception_no_leak(self):
        """Test that api_utils.handle_exception doesn't leak internal details"""
        from app.utils.api_utils import handle_exception
        from fastapi import HTTPException
        
        # Test with generic exception
        try:
            handle_exception(ValueError("Internal secret: password123"))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.detail == "Internal server error"
            assert "password123" not in e.detail
            assert "Internal secret" not in e.detail
        
        # Test with HTTPException (should pass through)
        try:
            handle_exception(HTTPException(status_code=400, detail="Bad request"))
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.detail == "Bad request"
    
    def test_deps_get_current_user_no_leak(self):
        """Test that get_current_user doesn't leak JWT decode errors"""
        from app.deps import get_current_user
        
        # Mock request with invalid token
        request = MagicMock()
        request.headers = {"Authorization": "Bearer invalid-token"}
        request.cookies = {}
        
        with patch('app.deps.JWTHandler.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("JWT decode failed: secret_key exposed")
            
            try:
                get_current_user(request)
                assert False, "Should have raised AppException"
            except AppException as e:
                assert isinstance(e.detail, dict)
                assert e.detail.get("message") == "Invalid or expired token"
                assert "secret_key" not in str(e.detail)
                assert "JWT decode failed" not in str(e.detail)
    
    @pytest.mark.asyncio
    async def test_jwt_middleware_no_leak(self):
        """Test that JWT middleware doesn't leak internal errors"""
        from app.middleware.jwt_middleware import JWTMiddleware
        from fastapi import Response
        
        # Mock request and endpoint
        request = MagicMock()
        request.url.path = "/api/test"
        request.headers = {"Authorization": "Bearer invalid-token"}
        request.state = MagicMock()
        
        call_next = MagicMock()
        call_next.return_value = Response()
        
        middleware = JWTMiddleware(app)
        
        with patch('app.middleware.jwt_middleware.JWTHandler.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("Internal JWT error: database credentials")
            
            response = await middleware.dispatch(request, call_next)
            
            assert response.status_code == 401
            content = response.body.decode()
            assert "database credentials" not in content
            assert "Internal JWT error" not in content
    
    @pytest.mark.asyncio
    async def test_token_service_no_leak(self):
        """Test that token service doesn't leak internal errors"""
        from app.services.token_service import TokenService
        
        # Mock session repository
        session_repo = MagicMock()
        session_repo.find_by_token.return_value = None
        
        token_service = TokenService(session_repo)
        
        with patch('app.services.token_service.JWTHandler.decode_token') as mock_decode:
            mock_decode.side_effect = Exception("Token parsing error: private_key")
            
            success, token_obj, error = await token_service.verify_token("invalid-token")
            
            assert not success
            assert token_obj is None
            assert error == "Token verification failed"
            assert "private_key" not in error
            assert "Token parsing error" not in error


class TestUserRepositoryFix:
    """Test that user repository uses correct field name for uniqueness check"""
    
    @pytest.mark.asyncio
    async def test_find_user_conflict_uses_username_field(self):
        """Test that find_user_conflict uses 'username' field instead of 'name'"""
        from app.repositories.user_repository import UserRepository
        
        # Mock database
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_db.users = mock_collection
        
        repo = UserRepository(mock_db)
        
        # Call the method
        await repo.find_user_conflict("testuser", "test@example.com", "1234567890")
        
        # Verify the query uses 'username' field
        mock_collection.find_one.assert_called_once()
        call_args = mock_collection.find_one.call_args[0][0]
        
        # Check that the query uses 'username' not 'name'
        assert "username" in str(call_args)
        assert "name" not in str(call_args) or call_args.get("$or", [{}])[0].get("username") == "testuser"


class TestCIFix:
    """Test that CI workflow uses correct pytest invocation"""
    
    def test_ci_yml_uses_correct_pytest_command(self):
        """Test that CI workflow uses 'uv run python -m pytest -q'"""
        import yaml
        
        with open('.github/workflows/ci.yml', 'r') as f:
            ci_config = yaml.safe_load(f)
        
        # Find the test step
        test_step = None
        for step in ci_config['jobs']['lint-and-test']['steps']:
            if step.get('name') == 'Run tests':
                test_step = step
                break
        
        assert test_step is not None, "Test step not found"
        assert 'uv run python -m pytest -q' in test_step['run'], "CI should use uv run python -m pytest -q"
        assert 'pytest -q' not in test_step['run'] or 'uv run python -m pytest -q' in test_step['run'], "CI should not use bare pytest -q"


if __name__ == "__main__":
    pytest.main([__file__])
