import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User, RoleEnum
from app.utils import hash_password

# Dùng SQLite file riêng cho test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_wood_factory.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Tạo user test
    admin_user = User(
        username="testadmin",
        hashed_password=hash_password("admin123"),
        full_name="Quản Trị Viên Test",
        role=RoleEnum.ADMIN,
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
