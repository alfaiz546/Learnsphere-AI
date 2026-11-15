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
    # Seed only the test database, never the configured application database.
    import app.database.base as base_mod
    import app.database.init_db as init_db_mod

    original_engine = base_mod.engine
    original_session_local = init_db_mod.SessionLocal

    try:
        base_mod.engine = test_engine
        init_db_mod.SessionLocal = TestingSessionLocal
        init_db_mod.init_db()
    finally:
        base_mod.engine = original_engine
        init_db_mod.SessionLocal = original_session_local
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
