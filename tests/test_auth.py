import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, verify_token, get_password_hash, verify_password
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate

# We'll use the client from conftest.py which will be set up properly

class TestAuth:
    """Test authentication functionality."""
    
    def test_create_access_token(self):
        """Test JWT token creation."""
        token = create_access_token(subject="123", is_admin=True)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["is_admin"] is True
    
    def test_verify_token_invalid(self):
        """Test token verification with invalid token."""
        payload = verify_token("invalid_token")
        assert payload is None
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_login_success(self, db_session: Session, client):
        """Test successful admin login."""
        # Create admin user
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        user_crud.create(db_session, obj_in=user_in)
        
        # Test login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["is_admin"] is True
    
    def test_login_wrong_password(self, db_session: Session, client):
        """Test login with wrong password."""
        # Create admin user
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        user_crud.create(db_session, obj_in=user_in)
        
        # Test login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        response_data = response.json()
        assert "Incorrect email or password" in response_data["error"]["message"]
    
    def test_login_non_admin(self, client: TestClient, db_session: Session):
        """Test login with non-admin user."""
        # Create regular user
        user_in = UserCreate(
            username="user",
            email="user@example.com",
            password="user123",
            is_admin=False,
            is_active=True
        )
        user_crud.create(db_session, obj_in=user_in)
        
        # Test login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "user123"
            }
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["error"]["message"]
    
    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """Test login with inactive user."""
        # Create inactive admin user
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=False
        )
        user_crud.create(db_session, obj_in=user_in)
        
        # Test login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["error"]["message"]
    
    def test_get_current_user(self, client: TestClient, db_session: Session):
        """Test getting current user info."""
        # Create admin user
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        created_user = user_crud.create(db_session, obj_in=user_in)
        
        # Create token
        token = create_access_token(subject=created_user.id, is_admin=True)
        
        # Test getting current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@example.com"
        assert data["username"] == "admin"
        assert data["is_admin"] is True
    
    def test_get_current_user_no_token(self, client):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_change_password(self, client: TestClient, db_session: Session):
        """Test changing password."""
        # Create admin user
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        created_user = user_crud.create(db_session, obj_in=user_in)
        
        # Create token
        token = create_access_token(subject=created_user.id, is_admin=True)
        
        # Test changing password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "admin123",
                "new_password": "new_password123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "Password updated successfully" in response.json()["message"]
        
        # Verify old password doesn't work
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin123"
            }
        )
        assert login_response.status_code == 401
        
        # Verify new password works
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "new_password123"
            }
        )
        assert login_response.status_code == 200
    
    def test_change_password_wrong_current(self, client: TestClient, db_session: Session):
        """Test changing password with wrong current password."""
        # Create admin user
        user_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        created_user = user_crud.create(db_session, obj_in=user_in)
        
        # Create token
        token = create_access_token(subject=created_user.id, is_admin=True)
        
        # Test changing password with wrong current password
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "wrong_password",
                "new_password": "new_password123"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["error"]["message"]

class TestUserManagement:
    """Test user management endpoints (admin only)."""
    
    def test_list_users(self, client: TestClient, db_session: Session):
        """Test listing users."""
        # Create admin user
        admin_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        admin_user = user_crud.create(db_session, obj_in=admin_in)
        
        # Create regular user
        user_in = UserCreate(
            username="user",
            email="user@example.com",
            password="user123",
            is_admin=False,
            is_active=True
        )
        user_crud.create(db_session, obj_in=user_in)
        
        # Create token
        token = create_access_token(subject=admin_user.id, is_admin=True)
        
        # Test listing users
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        emails = [user["email"] for user in data]
        assert "admin@example.com" in emails
        assert "user@example.com" in emails
    
    def test_create_user(self, client: TestClient, db_session: Session):
        """Test creating user."""
        # Create admin user
        admin_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        admin_user = user_crud.create(db_session, obj_in=admin_in)
        
        # Create token
        token = create_access_token(subject=admin_user.id, is_admin=True)
        
        # Test creating user
        response = client.post(
            "/api/v1/auth/users",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
                "is_admin": False,
                "is_active": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_admin"] is False
    
    def test_create_user_duplicate_email(self, client: TestClient, db_session: Session):
        """Test creating user with duplicate email."""
        # Create admin user
        admin_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        admin_user = user_crud.create(db_session, obj_in=admin_in)
        
        # Create token
        token = create_access_token(subject=admin_user.id, is_admin=True)
        
        # Test creating user with duplicate email
        response = client.post(
            "/api/v1/auth/users",
            json={
                "username": "newadmin",
                "email": "admin@example.com",  # Duplicate email
                "password": "password123",
                "is_admin": False,
                "is_active": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "User with this email already exists" in response.json()["error"]["message"]
    
    def test_update_user(self, client: TestClient, db_session: Session):
        """Test updating user."""
        # Create admin user
        admin_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        admin_user = user_crud.create(db_session, obj_in=admin_in)
        
        # Create regular user
        user_in = UserCreate(
            username="user",
            email="user@example.com",
            password="user123",
            is_admin=False,
            is_active=True
        )
        created_user = user_crud.create(db_session, obj_in=user_in)
        
        # Create token
        token = create_access_token(subject=admin_user.id, is_admin=True)
        
        # Test updating user
        response = client.put(
            f"/api/v1/auth/users/{created_user.id}",
            json={
                "full_name": "Updated User",
                "is_admin": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated User"
        assert data["is_admin"] is True
    
    def test_delete_user(self, client: TestClient, db_session: Session):
        """Test deleting user."""
        # Create admin user
        admin_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        admin_user = user_crud.create(db_session, obj_in=admin_in)
        
        # Create regular user
        user_in = UserCreate(
            username="user",
            email="user@example.com",
            password="user123",
            is_admin=False,
            is_active=True
        )
        created_user = user_crud.create(db_session, obj_in=user_in)
        
        # Create token
        token = create_access_token(subject=admin_user.id, is_admin=True)
        
        # Test deleting user
        response = client.delete(
            f"/api/v1/auth/users/{created_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "User deleted successfully" in response.json()["message"]
        
        # Verify user is deleted
        get_response = client.get(
            f"/api/v1/auth/users/{created_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 404
    
    def test_delete_self(self, client: TestClient, db_session: Session):
        """Test admin cannot delete themselves."""
        # Create admin user
        admin_in = UserCreate(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_admin=True,
            is_active=True
        )
        admin_user = user_crud.create(db_session, obj_in=admin_in)
        
        # Create token
        token = create_access_token(subject=admin_user.id, is_admin=True)
        
        # Test deleting self
        response = client.delete(
            f"/api/v1/auth/users/{admin_user.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["error"]["message"]
    
    def test_non_admin_access_denied(self, client: TestClient, db_session: Session):
        """Test non-admin users cannot access user management."""
        # Create regular user
        user_in = UserCreate(
            username="user",
            email="user@example.com",
            password="user123",
            is_admin=False,
            is_active=True
        )
        created_user = user_crud.create(db_session, obj_in=user_in)
        
        # Create token (non-admin)
        token = create_access_token(subject=created_user.id, is_admin=False)
        
        # Test accessing user list
        response = client.get(
            "/api/v1/auth/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Admin access required" in response.json()["error"]["message"]