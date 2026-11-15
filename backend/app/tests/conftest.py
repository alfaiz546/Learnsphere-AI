import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database.base import Base, get_db, engine as global_engine
from app.main import app

TEST_DB_URL = "sqlite:///./test_learnsphere.db"

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def test_db():
    # SQLite does not support schemas; strip schema-qualified table names
    # so that auth_security.* models can be created in the SQLite test DB.
    if test_engine.dialect.name == "sqlite":
        for _table in Base.metadata.tables.values():
            _table.schema = None
    Base.metadata.create_all(bind=test_engine)
    # Seed the test database using the same logic as init_db
    from app.database.init_db import init_db as init_db_func
    # Temporarily replace the global engine with the test engine for seeding
    original_engine = global_engine
    try:
        import app.database.base as base_mod
        base_mod.engine = test_engine
        init_db_func()
    finally:
        base_mod.engine = original_engine
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(test_db):
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
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
