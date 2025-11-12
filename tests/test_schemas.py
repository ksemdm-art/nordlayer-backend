import pytest
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from app.schemas import (
    User, UserCreate, UserUpdate,
    Project, ProjectCreate, ProjectUpdate, ProjectImage, ProjectImageCreate,
    Service, ServiceCreate, ServiceUpdate,
    Order, OrderCreate, OrderUpdate, OrderFile, OrderFileCreate,
    Article, ArticleCreate, ArticleUpdate,
    OrderStatus, OrderSource
)

class TestUserSchemas:
    def test_user_create_valid(self):
        """Test creating a user with valid data."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "securepassword123"
        assert user.full_name == "Test User"
        assert user.is_active is True

    def test_user_create_invalid_email(self):
        """Test that invalid email raises validation error."""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "value is not a valid email address" in str(exc_info.value)

    def test_user_update_partial(self):
        """Test partial user update."""
        update_data = {
            "full_name": "Updated Name",
            "is_active": False
        }
        user_update = UserUpdate(**update_data)
        
        assert user_update.full_name == "Updated Name"
        assert user_update.is_active is False
        assert user_update.username is None
        assert user_update.email is None

class TestProjectSchemas:
    def test_project_create_valid(self):
        """Test creating a project with valid data."""
        project_data = {
            "title": "Awesome 3D Model",
            "description": "A detailed description of the project",
            "category": "miniatures",
            "is_featured": True,
            "stl_file": "model.stl",
            "project_metadata": {"complexity": "high", "print_time": "4h"}
        }
        project = ProjectCreate(**project_data)
        
        assert project.title == "Awesome 3D Model"
        assert project.category == "miniatures"
        assert project.is_featured is True
        assert project.project_metadata["complexity"] == "high"

    def test_project_create_minimal(self):
        """Test creating a project with minimal required data."""
        project_data = {
            "title": "Simple Project",
            "category": "prototypes"
        }
        project = ProjectCreate(**project_data)
        
        assert project.title == "Simple Project"
        assert project.category == "prototypes"
        assert project.is_featured is False
        assert project.description is None
        assert project.stl_file is None

    def test_project_image_create(self):
        """Test creating a project image."""
        image_data = {
            "image_path": "/uploads/project_image.jpg",
            "alt_text": "Project main view",
            "is_primary": True
        }
        image = ProjectImageCreate(**image_data)
        
        assert image.image_path == "/uploads/project_image.jpg"
        assert image.alt_text == "Project main view"
        assert image.is_primary is True

class TestServiceSchemas:
    def test_service_create_valid(self):
        """Test creating a service with valid data."""
        service_data = {
            "name": "FDM Printing Service",
            "description": "High-quality FDM printing",
            "features": ["PLA", "ABS", "PETG"],
            "category": "printing",
            "is_active": True
        }
        service = ServiceCreate(**service_data)
        
        assert service.name == "FDM Printing Service"
        assert service.features == ["PLA", "ABS", "PETG"]
        assert service.is_active is True

    def test_service_create_minimal(self):
        """Test creating a service with minimal data."""
        service_data = {
            "name": "Basic Service"
        }
        service = ServiceCreate(**service_data)
        
        assert service.name == "Basic Service"
        assert service.is_active is True
        assert service.description is None
        assert service.features is None

class TestOrderSchemas:
    def test_order_create_valid(self):
        """Test creating an order with valid data."""
        order_data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "customer_contact": "john@example.com",
            "service_id": 1,
            "source": OrderSource.WEB,
            "specifications": {
                "material": "PLA",
                "infill": "20%",
                "layer_height": "0.2mm"
            },
            "notes": "Please print in blue color"
        }
        order = OrderCreate(**order_data)
        
        assert order.customer_name == "John Doe"
        assert order.customer_contact == "john@example.com"
        assert order.service_id == 1
        assert order.source == OrderSource.WEB
        assert order.specifications["material"] == "PLA"
        assert order.notes == "Please print in blue color"

    def test_order_create_telegram_source(self):
        """Test creating an order from Telegram."""
        order_data = {
            "customer_name": "Jane Smith",
            "customer_email": "jane@example.com",
            "customer_contact": "@janesmith",
            "service_id": 2,
            "source": OrderSource.TELEGRAM,
            "customer_id": 123
        }
        order = OrderCreate(**order_data)
        
        assert order.source == OrderSource.TELEGRAM
        assert order.customer_contact == "@janesmith"
        assert order.customer_id == 123

    def test_order_update_status(self):
        """Test updating order status."""
        update_data = {
            "status": OrderStatus.IN_PROGRESS,
            "total_price": Decimal("45.50"),
            "notes": "Started printing"
        }
        order_update = OrderUpdate(**update_data)
        
        assert order_update.status == OrderStatus.IN_PROGRESS
        assert order_update.total_price == Decimal("45.50")
        assert order_update.notes == "Started printing"

    def test_order_file_create(self):
        """Test creating an order file."""
        file_data = {
            "file_path": "/uploads/order_123/model.stl",
            "original_filename": "my_awesome_model.stl",
            "file_size": 2048000,
            "file_type": "application/octet-stream"
        }
        order_file = OrderFileCreate(**file_data)
        
        assert order_file.file_path == "/uploads/order_123/model.stl"
        assert order_file.original_filename == "my_awesome_model.stl"
        assert order_file.file_size == 2048000
        assert order_file.file_type == "application/octet-stream"

class TestArticleSchemas:
    def test_article_create_valid(self):
        """Test creating an article with valid data."""
        article_data = {
            "title": "Getting Started with 3D Printing",
            "content": "This comprehensive guide will teach you...",
            "excerpt": "Learn the basics of 3D printing",
            "category": "tutorials",
            "slug": "getting-started-3d-printing",
            "is_published": True,
            "published_at": datetime.utcnow(),
            "featured_image": "/images/3d-printing-guide.jpg"
        }
        article = ArticleCreate(**article_data)
        
        assert article.title == "Getting Started with 3D Printing"
        assert article.category == "tutorials"
        assert article.slug == "getting-started-3d-printing"
        assert article.is_published is True

    def test_article_create_draft(self):
        """Test creating a draft article."""
        article_data = {
            "title": "Draft Article",
            "content": "This is a draft...",
            "category": "news",
            "slug": "draft-article",
            "is_published": False
        }
        article = ArticleCreate(**article_data)
        
        assert article.is_published is False
        assert article.published_at is None
        assert article.excerpt is None

    def test_article_update_partial(self):
        """Test partial article update."""
        update_data = {
            "title": "Updated Title",
            "is_published": True,
            "published_at": datetime.utcnow()
        }
        article_update = ArticleUpdate(**update_data)
        
        assert article_update.title == "Updated Title"
        assert article_update.is_published is True
        assert article_update.content is None
        assert article_update.category is None

class TestEnumValidation:
    def test_order_status_enum(self):
        """Test OrderStatus enum validation."""
        # Valid status
        order_data = {
            "customer_name": "Test",
            "customer_email": "test@example.com",
            "customer_contact": "test@example.com",
            "service_id": 1,
            "source": OrderSource.WEB
        }
        order = OrderCreate(**order_data)
        
        update_data = {"status": OrderStatus.COMPLETED}
        update = OrderUpdate(**update_data)
        assert update.status == OrderStatus.COMPLETED

    def test_order_source_enum(self):
        """Test OrderSource enum validation."""
        order_data = {
            "customer_name": "Test",
            "customer_email": "test@example.com",
            "customer_contact": "test@example.com",
            "service_id": 1,
            "source": OrderSource.TELEGRAM
        }
        order = OrderCreate(**order_data)
        assert order.source == OrderSource.TELEGRAM

    def test_invalid_enum_value(self):
        """Test that invalid enum values raise validation error."""
        with pytest.raises(ValidationError):
            OrderUpdate(status="invalid_status")

class TestSchemaValidation:
    def test_required_fields_missing(self):
        """Test that missing required fields raise validation errors."""
        # Missing required fields for UserCreate
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="test")  # Missing email and password
        
        errors = exc_info.value.errors()
        error_fields = [error["loc"][0] for error in errors]
        assert "email" in error_fields
        assert "password" in error_fields

    def test_decimal_precision(self):
        """Test decimal field precision validation."""
        service_data = {
            "name": "Test Service",
            "features": ["feature1", "feature2"]
        }
        service = ServiceCreate(**service_data)
        assert service.features == ["feature1", "feature2"]
        assert isinstance(service.features, list)

    def test_json_field_validation(self):
        """Test JSON field validation."""
        project_data = {
            "title": "Test Project",
            "category": "test",
            "project_metadata": {
                "complexity": "medium",
                "materials": ["PLA", "ABS"],
                "settings": {
                    "layer_height": 0.2,
                    "infill": 20
                }
            }
        }
        project = ProjectCreate(**project_data)
        
        assert project.project_metadata["complexity"] == "medium"
        assert "PLA" in project.project_metadata["materials"]
        assert project.project_metadata["settings"]["layer_height"] == 0.2