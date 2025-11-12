import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Project, ProjectImage, Service, Order, OrderFile, Article
from app.schemas.base import OrderStatus, OrderSource

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

class TestUserModel:
    def test_create_user(self, db_session):
        """Test creating a user with valid data."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_123",
            full_name="Test User",
            is_active=True,
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_unique_constraints(self, db_session):
        """Test that username and email must be unique."""
        user1 = User(
            username="testuser",
            email="test@example.com",
            hashed_password="password1"
        )
        user2 = User(
            username="testuser",  # Same username
            email="different@example.com",
            hashed_password="password2"
        )
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

class TestProjectModel:
    def test_create_project(self, db_session):
        """Test creating a project with valid data."""
        project = Project(
            title="Test Project",
            description="A test 3D printing project",
            category="miniatures",
            stl_file="test_model.stl",
            is_featured=True,
            project_metadata={"complexity": "medium", "print_time": "2h"}
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.id is not None
        assert project.title == "Test Project"
        assert project.category == "miniatures"
        assert project.is_featured is True
        assert project.project_metadata["complexity"] == "medium"

    def test_project_with_images(self, db_session):
        """Test project with associated images."""
        project = Project(
            title="Project with Images",
            category="prototypes",
            images=[
                "/images/project1_main.jpg",
                "/images/project1_side.jpg"
            ]
        )
        db_session.add(project)
        db_session.commit()
        
        assert len(project.images) == 2
        assert "/images/project1_main.jpg" in project.images
        assert "/images/project1_side.jpg" in project.images

class TestServiceModel:
    def test_create_service(self, db_session):
        """Test creating a service with valid data."""
        service = Service(
            name="FDM Printing",
            description="High-quality FDM 3D printing service",
            features={
                "material_options": ["PLA", "ABS", "PETG"],
                "size_options": ["small", "medium", "large"]
            },
            is_active=True,
            category="printing"
        )
        db_session.add(service)
        db_session.commit()
        
        assert service.id is not None
        assert service.name == "FDM Printing"
        assert service.is_active == True
        assert service.features["material_options"] == ["PLA", "ABS", "PETG"]

class TestOrderModel:
    def test_create_order(self, db_session):
        """Test creating an order with valid data."""
        # First create a service
        service = Service(
            name="Test Service",
            is_active=True
        )
        db_session.add(service)
        db_session.flush()
        
        order = Order(
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_contact="john@example.com",
            service_id=service.id,
            specifications={"material": "PLA", "infill": "20%"},
            status="new",
            source="web",
            notes="Rush order"
        )
        db_session.add(order)
        db_session.commit()
        
        assert order.id is not None
        assert order.customer_name == "John Doe"
        assert order.status == "new"
        assert order.source == "web"
        assert order.specifications["material"] == "PLA"

    def test_order_with_files(self, db_session):
        """Test order with associated files."""
        service = Service(name="Test Service")
        db_session.add(service)
        db_session.flush()
        
        order = Order(
            customer_name="Jane Doe",
            customer_email="jane@example.com",
            customer_contact="jane@example.com",
            service_id=service.id,
            status="new",
            source="telegram"
        )
        db_session.add(order)
        db_session.flush()
        
        file1 = OrderFile(
            order_id=order.id,
            file_path="/uploads/model1.stl",
            original_filename="my_model.stl",
            file_size=1024000,
            file_type="application/octet-stream"
        )
        file2 = OrderFile(
            order_id=order.id,
            file_path="/uploads/reference.jpg",
            original_filename="reference_image.jpg",
            file_size=512000,
            file_type="image/jpeg"
        )
        
        db_session.add_all([file1, file2])
        db_session.commit()
        
        assert len(order.files) == 2
        assert order.files[0].original_filename == "my_model.stl"
        assert order.files[1].file_type == "image/jpeg"

class TestArticleModel:
    def test_create_article(self, db_session):
        """Test creating an article with valid data."""
        # First create an author
        author = User(
            username="author",
            email="author@example.com",
            hashed_password="password"
        )
        db_session.add(author)
        db_session.flush()
        
        article = Article(
            title="Introduction to 3D Printing",
            content="This is a comprehensive guide to 3D printing...",
            excerpt="Learn the basics of 3D printing technology",
            category="tutorials",
            slug="introduction-to-3d-printing",
            is_published=True,
            published_at=datetime.utcnow()
        )
        db_session.add(article)
        db_session.commit()
        
        assert article.id is not None
        assert article.title == "Introduction to 3D Printing"
        assert article.category == "tutorials"
        assert article.is_published is True
        assert article.slug == "introduction-to-3d-printing"

    def test_article_slug_unique(self, db_session):
        """Test that article slugs must be unique."""
        author = User(
            username="author",
            email="author@example.com",
            hashed_password="password"
        )
        db_session.add(author)
        db_session.flush()
        
        article1 = Article(
            title="First Article",
            content="Content 1",
            category="tutorials",
            slug="same-slug"
        )
        article2 = Article(
            title="Second Article",
            content="Content 2",
            category="tutorials",
            slug="same-slug"  # Same slug
        )
        
        db_session.add(article1)
        db_session.commit()
        
        db_session.add(article2)
        with pytest.raises(Exception):  # Should raise integrity error
            db_session.commit()

class TestModelRelationships:
    def test_user_orders_relationship(self, db_session):
        """Test the relationship between users and orders."""
        user = User(
            username="customer",
            email="customer@example.com",
            hashed_password="password"
        )
        service = Service(name="Test Service")
        db_session.add_all([user, service])
        db_session.flush()
        
        order = Order(
            customer_name="Customer Name",
            customer_email="customer@example.com",
            customer_contact="customer@example.com",
            service_id=service.id,
            customer_id=user.id,
            status="new",
            source="web"
        )
        db_session.add(order)
        db_session.commit()
        
        assert len(user.orders) == 1
        assert user.orders[0].customer_name == "Customer Name"
        assert order.customer.username == "customer"

    def test_service_orders_relationship(self, db_session):
        """Test the relationship between services and orders."""
        service = Service(
            name="Premium Service"
        )
        db_session.add(service)
        db_session.flush()
        
        order1 = Order(
            customer_name="Customer 1",
            customer_email="customer1@example.com",
            customer_contact="customer1@example.com",
            service_id=service.id,
            status="new",
            source="web"
        )
        order2 = Order(
            customer_name="Customer 2",
            customer_email="customer2@example.com",
            customer_contact="customer2@example.com",
            service_id=service.id,
            status="in_progress",
            source="telegram"
        )
        
        db_session.add_all([order1, order2])
        db_session.commit()
        
        assert len(service.orders) == 2
        assert service.orders[0].customer_name == "Customer 1"
        assert service.orders[1].source == "telegram"