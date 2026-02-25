"""
Authentication API Tests
"""
import pytest
from fastapi import status


class TestAuthRegistration:
    """Test user registration"""
    
    def test_register_customer_success(self, client, test_store):
        """Test successful customer registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "StrongPassword123!",
                "full_name": "New User",
                "phone": "5555555555"
            },
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
    
    def test_register_duplicate_email(self, client, test_store, test_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "AnotherPassword123!",
                "full_name": "Another User",
                "phone": "1111111111"
            },
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_weak_password(self, client, test_store):
        """Test registration with weak password"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "123",  # Too short
                "full_name": "Weak User",
                "phone": "2222222222"
            },
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Test user login"""
    
    def test_login_success(self, client, test_store, test_user):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            },
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == test_user.email
    
    def test_login_wrong_password(self, client, test_store, test_user):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            },
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client, test_store):
        """Test login with nonexistent user"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword"
            },
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthUserProfile:
    """Test user profile operations"""
    
    def test_get_current_user(self, client, auth_headers, test_user, test_store):
        """Test getting current user info"""
        response = client.get(
            "/api/v1/auth/me",
            headers={**auth_headers, "X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
    
    def test_get_current_user_unauthorized(self, client, test_store):
        """Test getting user info without token"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile(self, client, auth_headers, test_store):
        """Test updating user profile"""
        response = client.put(
            "/api/v1/auth/me",
            json={"full_name": "Updated Name"},
            headers={**auth_headers, "X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["full_name"] == "Updated Name"
    
    def test_change_password(self, client, auth_headers, test_store):
        """Test changing password"""
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "testpassword123",
                "new_password": "NewPassword456!"
            },
            headers={**auth_headers, "X-Store-ID": str(test_store.id)}
        )
        assert response.status_code == status.HTTP_200_OK
