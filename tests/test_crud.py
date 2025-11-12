import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.schemas.base import OrderStatus, OrderSource
from app.crud import user, project, service, order, article
from app.schemas import (
    UserCreate, UserUpdate,
    ProjectCreate, ProjectUpdate,
    ServiceCreate, ServiceUpdate,
    OrderCreate, OrderUpdate,
    ArticleCreate, ArticleUpdate
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_crud.db"
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

class TestUserCRUD:
    def test_create_user(self, db_session):
        """Test creating a user."""
        user_in = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )
        created_user = user.create(db_session, obj_in=user_in)
        
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        assert created_user.full_name == "Test User"
        assert created_user.hashed_password != "testpassword123"  # Should be hashed
        assert created_user.is_active is True
        assert created_user.is_admin is False

    def test_get_user_by_email(self, db_session):
        """Test getting user by email."""
        user_in = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = user.create(db_session, obj_in=user_in)
        
        retrieved_user = user.get_by_email(db_session, email="test@example.com")
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == "test@example.com"

    def test_authenticate_user(self, db_session):
        """Test user authentication."""
        user_in = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = user.create(db_session, obj_in=user_in)
        
        # Test correct password
        authenticated_user = user.authenticate(
            db_session, email="test@example.com", password="testpassword123"
        )
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id
        
        # Test wrong password
        wrong_auth = user.authenticate(
            db_session, email="test@example.com", password="wrongpassword"
        )
        assert wrong_auth is None

    def test_update_user(self, db_session):
        """Test updating a user."""
        user_in = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = user.create(db_session, obj_in=user_in)
        
        user_update = UserUpdate(full_name="Updated Name", is_active=False)
        updated_user = user.update(db_session, db_obj=created_user, obj_in=user_update)
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.is_active is False
        assert updated_user.username == "testuser"  # Unchanged

class TestProjectCRUD:
    def test_create_project(self, db_session):
        """Test creating a project."""
        project_in = ProjectCreate(
            title="Test Project",
            description="A test 3D printing project",
            category="miniatures",
            stl_file="test_model.stl",
            is_featured=True
        )
        created_project = project.create(db_session, obj_in=project_in)
        
        assert created_project.title == "Test Project"
        assert created_project.category == "miniatures"
        assert created_project.is_featured is True
        assert created_project.stl_file == "test_model.stl"

    def test_get_projects_by_category(self, db_session):
        """Test getting projects by category."""
        # Create projects in different categories
        project1 = ProjectCreate(title="Miniature 1", category="miniatures")
        project2 = ProjectCreate(title="Prototype 1", category="prototypes")
        project3 = ProjectCreate(title="Miniature 2", category="miniatures")
        
        project.create(db_session, obj_in=project1)
        project.create(db_session, obj_in=project2)
        project.create(db_session, obj_in=project3)
        
        miniatures = project.get_by_category(db_session, category="miniatures")
        assert len(miniatures) == 2
        assert all(p.category == "miniatures" for p in miniatures)

    def test_get_featured_projects(self, db_session):
        """Test getting featured projects."""
        project1 = ProjectCreate(title="Featured 1", category="test", is_featured=True)
        project2 = ProjectCreate(title="Regular 1", category="test", is_featured=False)
        project3 = ProjectCreate(title="Featured 2", category="test", is_featured=True)
        
        project.create(db_session, obj_in=project1)
        project.create(db_session, obj_in=project2)
        project.create(db_session, obj_in=project3)
        
        featured = project.get_featured(db_session)
        assert len(featured) == 2
        assert all(p.is_featured for p in featured)

class TestServiceCRUD:
    def test_create_service(self, db_session):
        """Test creating a service."""
        service_in = ServiceCreate(
            name="FDM Printing",
            description="High-quality FDM printing service",
            features=["PLA", "ABS", "PETG"],
            category="printing"
        )
        created_service = service.create(db_session, obj_in=service_in)
        
        assert created_service.name == "FDM Printing"
        assert created_service.features == ["PLA", "ABS", "PETG"]
        assert created_service.is_active is True

    def test_get_active_services(self, db_session):
        """Test getting active services."""
        service1 = ServiceCreate(name="Active Service", is_active=True)
        service2 = ServiceCreate(name="Inactive Service", is_active=False)
        
        service.create(db_session, obj_in=service1)
        service.create(db_session, obj_in=service2)
        
        active_services = service.get_active(db_session)
        assert len(active_services) == 1
        assert active_services[0].name == "Active Service"

    def test_deactivate_service(self, db_session):
        """Test deactivating a service."""
        service_in = ServiceCreate(name="Test Service")
        created_service = service.create(db_session, obj_in=service_in)
        
        assert created_service.is_active is True
        
        deactivated = service.deactivate(db_session, id=created_service.id)
        assert deactivated.is_active is False

class TestOrderCRUD:
    def test_create_order(self, db_session):
        """Test creating an order."""
        # First create a service
        service_in = ServiceCreate(name="Test Service")
        created_service = service.create(db_session, obj_in=service_in)
        
        order_in = OrderCreate(
            customer_name="John Doe",
            customer_email="john@example.com",
            customer_contact="john@example.com",
            service_id=created_service.id,
            source=OrderSource.WEB,
            specifications={"material": "PLA", "infill": "20%"}
        )
        created_order = order.create(db_session, obj_in=order_in)
        
        assert created_order.customer_name == "John Doe"
        assert created_order.service_id == created_service.id
        assert created_order.source == OrderSource.WEB
        assert created_order.status == OrderStatus.NEW
        assert created_order.specifications["material"] == "PLA"

    def test_get_orders_by_status(self, db_session):
        """Test getting orders by status."""
        # Create a service first
        service_in = ServiceCreate(name="Test Service")
        created_service = service.create(db_session, obj_in=service_in)
        
        # Create orders with different statuses
        order1 = OrderCreate(
            customer_name="Customer 1",
            customer_email="customer1@example.com",
            customer_contact="customer1@example.com",
            service_id=created_service.id,
            source=OrderSource.WEB
        )
        order2 = OrderCreate(
            customer_name="Customer 2",
            customer_email="customer2@example.com",
            customer_contact="customer2@example.com",
            service_id=created_service.id,
            source=OrderSource.TELEGRAM
        )
        
        created_order1 = order.create(db_session, obj_in=order1)
        created_order2 = order.create(db_session, obj_in=order2)
        
        # Update one order status
        order.update_status(db_session, order_id=created_order1.id, status=OrderStatus.IN_PROGRESS)
        
        # Test getting orders by status
        new_orders = order.get_by_status(db_session, status=OrderStatus.NEW)
        in_progress_orders = order.get_by_status(db_session, status=OrderStatus.IN_PROGRESS)
        
        assert len(new_orders) == 1
        assert len(in_progress_orders) == 1
        assert new_orders[0].customer_name == "Customer 2"
        assert in_progress_orders[0].customer_name == "Customer 1"

    def test_update_order_status(self, db_session):
        """Test updating order status."""
        # Create service and order
        service_in = ServiceCreate(name="Test Service")
        created_service = service.create(db_session, obj_in=service_in)
        
        order_in = OrderCreate(
            customer_name="Test Customer",
            customer_email="test@example.com",
            customer_contact="test@example.com",
            service_id=created_service.id,
            source=OrderSource.WEB
        )
        created_order = order.create(db_session, obj_in=order_in)
        
        assert created_order.status == OrderStatus.NEW
        
        # Update status
        updated_order = order.update_status(
            db_session, order_id=created_order.id, status=OrderStatus.COMPLETED
        )
        assert updated_order.status == OrderStatus.COMPLETED

class TestArticleCRUD:
    def test_create_article(self, db_session):
        """Test creating an article."""
        # First create an author
        user_in = UserCreate(
            username="author",
            email="author@example.com",
            password="password123"
        )
        created_user = user.create(db_session, obj_in=user_in)
        
        article_in = ArticleCreate(
            title="Test Article",
            content="This is a test article content.",
            excerpt="Test excerpt",
            category="tutorials",
            slug="test-article",
            is_published=True
        )
        created_article = article.create(db_session, obj_in=article_in)
        
        assert created_article.title == "Test Article"
        assert created_article.category == "tutorials"
        assert created_article.slug == "test-article"
        assert created_article.is_published is True

    def test_get_article_by_slug(self, db_session):
        """Test getting article by slug."""
        # Create author and article
        user_in = UserCreate(username="author", email="author@example.com", password="password123")
        created_user = user.create(db_session, obj_in=user_in)
        
        article_in = ArticleCreate(
            title="Unique Article",
            content="Content",
            category="test",
            slug="unique-article"
        )
        created_article = article.create(db_session, obj_in=article_in)
        
        retrieved_article = article.get_by_slug(db_session, slug="unique-article")
        assert retrieved_article.id == created_article.id
        assert retrieved_article.title == "Unique Article"

    def test_get_published_articles(self, db_session):
        """Test getting published articles."""
        # Create author
        user_in = UserCreate(username="author", email="author@example.com", password="password123")
        created_user = user.create(db_session, obj_in=user_in)
        
        # Create published and unpublished articles
        article1 = ArticleCreate(
            title="Published Article",
            content="Content",
            category="test",
            slug="published-article",
            is_published=True
        )
        article2 = ArticleCreate(
            title="Draft Article",
            content="Content",
            category="test",
            slug="draft-article",
            is_published=False
        )
        
        article.create(db_session, obj_in=article1)
        article.create(db_session, obj_in=article2)
        
        published_articles = article.get_published(db_session)
        assert len(published_articles) == 1
        assert published_articles[0].title == "Published Article"

    def test_publish_article(self, db_session):
        """Test publishing an article."""
        # Create author and draft article
        user_in = UserCreate(username="author", email="author@example.com", password="password123")
        created_user = user.create(db_session, obj_in=user_in)
        
        article_in = ArticleCreate(
            title="Draft Article",
            content="Content",
            category="test",
            slug="draft-article",
            is_published=False
        )
        created_article = article.create(db_session, obj_in=article_in)
        
        assert created_article.is_published is False
        assert created_article.published_at is None
        
        # Publish the article
        published_article = article.publish(db_session, article_id=created_article.id)
        assert published_article.is_published is True
        assert published_article.published_at is not None