"""
Tests for projects API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from app.main import app
from app.core.database import get_db
from app.models.project import Project, ProjectImage
from app.services.project import project_service


client = TestClient(app)


# Mock database session
@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


# Override dependency
def override_get_db():
    return MagicMock(spec=Session)


app.dependency_overrides[get_db] = override_get_db


class TestProjectsAPI:
    """Test projects API endpoints"""
    
    def test_get_projects_list(self):
        """Test getting paginated list of projects"""
        with patch.object(project_service, 'get_projects_with_filters') as mock_get, \
             patch.object(project_service, 'count_projects_with_filters') as mock_count:
            
            # Create more realistic mock data
            mock_project1 = MagicMock()
            mock_project1.id = 1
            mock_project1.title = "Test Project 1"
            mock_project1.description = "Test Description 1"
            mock_project1.category = "miniatures"
            mock_project1.is_featured = True
            mock_project1.stl_file = None
            mock_project1.project_metadata = {}
            mock_project1.created_at = "2024-01-01T00:00:00"
            mock_project1.updated_at = "2024-01-01T00:00:00"
            mock_project1.estimated_price = 25.50
            mock_project1.complexity_level = "medium"
            mock_project1.price_range_min = 20.00
            mock_project1.price_range_max = 30.00
            
            mock_project2 = MagicMock()
            mock_project2.id = 2
            mock_project2.title = "Test Project 2"
            mock_project2.description = "Test Description 2"
            mock_project2.category = "prototypes"
            mock_project2.is_featured = False
            mock_project2.stl_file = None
            mock_project2.project_metadata = {}
            mock_project2.created_at = "2024-01-01T00:00:00"
            mock_project2.updated_at = "2024-01-01T00:00:00"
            mock_project2.estimated_price = 15.00
            mock_project2.complexity_level = "simple"
            mock_project2.price_range_min = 10.00
            mock_project2.price_range_max = 20.00
            
            mock_projects = [mock_project1, mock_project2]
            mock_get.return_value = mock_projects
            mock_count.return_value = 2
            
            response = client.get("/api/v1/projects/")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert len(data["data"]) == 2
            assert "pagination" in data
            assert data["pagination"]["total"] == 2
    
    def test_get_projects_with_filters(self):
        """Test getting projects with filters"""
        with patch.object(project_service, 'get_projects_with_filters') as mock_get, \
             patch.object(project_service, 'count_projects_with_filters') as mock_count:
            
            mock_get.return_value = []
            mock_count.return_value = 0
            
            response = client.get(
                "/api/v1/projects/",
                params={
                    "category": "miniatures",
                    "is_featured": True,
                    "search": "dragon",
                    "page": 1,
                    "per_page": 10
                }
            )
            
            assert response.status_code == 200
            
            # Verify service was called with correct parameters
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args.kwargs["category"] == "miniatures"
            assert call_args.kwargs["is_featured"] == True
            assert call_args.kwargs["search"] == "dragon"
            assert call_args.kwargs["skip"] == 0
            assert call_args.kwargs["limit"] == 10
    
    def test_get_featured_projects(self):
        """Test getting featured projects"""
        with patch.object(project_service, 'get_featured_projects') as mock_get:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.title = "Featured Project"
            mock_project.description = "Featured Description"
            mock_project.category = "miniatures"
            mock_project.is_featured = True
            mock_project.stl_file = None
            mock_project.project_metadata = {}
            mock_project.created_at = "2024-01-01T00:00:00"
            mock_project.updated_at = "2024-01-01T00:00:00"
            mock_project.estimated_price = 35.00
            mock_project.complexity_level = "complex"
            mock_project.price_range_min = 30.00
            mock_project.price_range_max = 40.00
            
            mock_projects = [mock_project]
            mock_get.return_value = mock_projects
            
            response = client.get("/api/v1/projects/featured")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert len(data["data"]) == 1
            
            mock_get.assert_called_once_with(mock_get.call_args[0][0], limit=10)
    
    def test_get_project_categories(self):
        """Test getting project categories"""
        with patch.object(project_service, 'get_available_categories') as mock_get:
            mock_categories = ["miniatures", "prototypes", "jewelry"]
            mock_get.return_value = mock_categories
            
            response = client.get("/api/v1/projects/categories")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"] == mock_categories
    
    def test_get_project_by_id(self):
        """Test getting a specific project"""
        with patch.object(project_service, 'get_project_with_images') as mock_get:
            mock_project = MagicMock()
            mock_project.id = 1
            mock_project.title = "Test Project"
            mock_project.description = "Test Description"
            mock_project.category = "miniatures"
            mock_project.is_featured = False
            mock_project.stl_file = None
            mock_project.project_metadata = {}
            mock_project.created_at = "2024-01-01T00:00:00"
            mock_project.updated_at = "2024-01-01T00:00:00"
            mock_project.images = []
            mock_project.estimated_price = 25.00
            mock_project.complexity_level = "medium"
            mock_project.price_range_min = 20.00
            mock_project.price_range_max = 30.00
            
            mock_get.return_value = mock_project
            
            response = client.get("/api/v1/projects/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "data" in data
            
            mock_get.assert_called_once_with(mock_get.call_args[0][0], 1)
    
    def test_get_project_not_found(self):
        """Test getting a non-existent project"""
        with patch.object(project_service, 'get_project_with_images') as mock_get:
            from app.core.exceptions import NotFoundError
            mock_get.side_effect = NotFoundError("Project", 999)
            
            response = client.get("/api/v1/projects/999")
            
            assert response.status_code == 404
    
    def test_get_project_stl_file(self):
        """Test downloading STL file"""
        with patch.object(project_service, 'get_or_404') as mock_get, \
             patch('pathlib.Path.exists') as mock_exists:
            
            # Create a temporary file for testing
            with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as temp_file:
                temp_file.write(b"STL content")
                temp_path = temp_file.name
            
            try:
                mock_project = MagicMock(
                    id=1,
                    title="Test Project",
                    stl_file=temp_path
                )
                mock_get.return_value = mock_project
                mock_exists.return_value = True
                
                response = client.get("/api/v1/projects/1/stl")
                
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/octet-stream"
                
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
    
    def test_get_project_stl_file_not_available(self):
        """Test downloading STL file when not available"""
        with patch.object(project_service, 'get_or_404') as mock_get:
            mock_project = MagicMock(id=1, stl_file=None)
            mock_get.return_value = mock_project
            
            response = client.get("/api/v1/projects/1/stl")
            
            assert response.status_code == 404
            response_data = response.json()
            # Check if it's our custom error format or FastAPI's default
            if "detail" in response_data:
                assert "STL file not available" in response_data["detail"]
            elif "error" in response_data:
                assert "STL file not available" in response_data["error"]["message"]


class TestProjectsAPIAdmin:
    """Test admin-only project endpoints"""
    
    def test_create_project_without_auth(self):
        """Test creating project without authentication"""
        project_data = {
            "title": "New Project",
            "description": "Test Description",
            "category": "miniatures"
        }
        
        response = client.post("/api/v1/projects/", json=project_data)
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_update_project_without_auth(self):
        """Test updating project without authentication"""
        project_data = {
            "title": "Updated Project"
        }
        
        response = client.put("/api/v1/projects/1", json=project_data)
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_delete_project_without_auth(self):
        """Test deleting project without authentication"""
        response = client.delete("/api/v1/projects/1")
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_upload_stl_without_auth(self):
        """Test uploading STL file without authentication"""
        with tempfile.NamedTemporaryFile(suffix='.stl') as temp_file:
            temp_file.write(b"STL content")
            temp_file.seek(0)
            
            response = client.post(
                "/api/v1/projects/1/stl",
                files={"file": ("test.stl", temp_file, "application/octet-stream")}
            )
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_upload_image_without_auth(self):
        """Test uploading image without authentication"""
        with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
            temp_file.write(b"JPEG content")
            temp_file.seek(0)
            
            response = client.post(
                "/api/v1/projects/1/images",
                files={"file": ("test.jpg", temp_file, "image/jpeg")}
            )
        
        # Should require authentication
        assert response.status_code in [401, 403]


class TestProjectsAPIValidation:
    """Test API validation"""
    
    def test_get_projects_invalid_pagination(self):
        """Test invalid pagination parameters"""
        # Page must be >= 1
        response = client.get("/api/v1/projects/?page=0")
        assert response.status_code == 422
        
        # Per page must be <= 100
        response = client.get("/api/v1/projects/?per_page=101")
        assert response.status_code == 422
    
    def test_get_featured_projects_invalid_limit(self):
        """Test invalid limit for featured projects"""
        # Limit must be <= 50
        response = client.get("/api/v1/projects/featured?limit=51")
        assert response.status_code == 422
        
        # Limit must be >= 1
        response = client.get("/api/v1/projects/featured?limit=0")
        assert response.status_code == 422


class TestProjectService:
    """Test project service methods"""
    
    def test_get_projects_with_filters(self, mock_db):
        """Test service method for getting projects with filters"""
        # Mock query chain
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        result = project_service.get_projects_with_filters(
            mock_db,
            skip=0,
            limit=10,
            category="miniatures",
            is_featured=True,
            search="dragon"
        )
        
        assert result == []
        mock_db.query.assert_called_once_with(Project)
    
    def test_count_projects_with_filters(self, mock_db):
        """Test service method for counting projects with filters"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        
        result = project_service.count_projects_with_filters(
            mock_db,
            category="miniatures"
        )
        
        assert result == 5
        mock_db.query.assert_called_once_with(Project)
    
    def test_get_available_categories(self, mock_db):
        """Test getting available categories"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [("miniatures",), ("prototypes",), ("jewelry",)]
        
        result = project_service.get_available_categories(mock_db)
        
        assert result == ["miniatures", "prototypes", "jewelry"]
    
    def test_add_image_to_project(self, mock_db):
        """Test adding image to project"""
        # Mock project exists
        mock_project = MagicMock(id=1)
        with patch.object(project_service, 'get_or_404', return_value=mock_project):
            
            # Mock query for updating primary images
            mock_query = MagicMock()
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.update.return_value = None
            
            result = project_service.add_image_to_project(
                mock_db,
                project_id=1,
                image_path="/path/to/image.jpg",
                alt_text="Test image",
                is_primary=True
            )
            
            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()