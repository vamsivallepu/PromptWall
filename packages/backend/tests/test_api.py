"""Integration tests for API endpoints"""
import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.db_models import LogEntryDB, FirewallConfigDB, UserDB
from app.auth import get_password_hash, create_access_token

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Override database dependency for tests"""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
async def client():
    """Create test client"""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=True) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def setup_database():
    """Setup test database before each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create test user
    async with TestSessionLocal() as session:
        test_user = UserDB(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            full_name="Test User",
            is_active=True,
            is_admin=True
        )
        session.add(test_user)
        await session.commit()
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def auth_token():
    """Create test authentication token"""
    token = create_access_token(
        data={
            "sub": "testuser",
            "user_id": "test-user-id",
            "is_admin": True
        }
    )
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


# Test log ingestion endpoint
@pytest.mark.asyncio
async def test_upload_logs_valid(client, auth_headers):
    """Test uploading valid log entries"""
    log_data = {
        "deviceId": "device-123",
        "logs": [
            {
                "id": "log-1",
                "timestamp": datetime.utcnow().isoformat(),
                "deviceId": "device-123",
                "userId": "user-1",
                "toolName": "ChatGPT",
                "toolType": "web",
                "riskLevel": "amber",
                "promptLength": 150,
                "detectedEntityTypes": ["email", "person"],
                "entityCount": 2,
                "wasSanitized": True,
                "metadata": {
                    "browserVersion": "Chrome 120",
                    "osVersion": "Windows 11",
                    "agentVersion": "1.0.0"
                }
            }
        ]
    }
    
    response = await client.post(
        "/api/v1/logs/batch",
        json=log_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 1


@pytest.mark.asyncio
async def test_upload_logs_invalid_data(client, auth_headers):
    """Test uploading invalid log entries"""
    log_data = {
        "deviceId": "device-123",
        "logs": [
            {
                "id": "log-1",
                # Missing required fields
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]
    }
    
    response = await client.post(
        "/api/v1/logs/batch",
        json=log_data,
        headers=auth_headers
    )
    
    assert response.status_code == 422  # Validation error


# Test log query endpoint
@pytest.mark.asyncio
async def test_get_logs_with_filters(client, auth_headers):
    """Test querying logs with various filters"""
    # Insert test logs
    async with TestSessionLocal() as session:
        logs = [
            LogEntryDB(
                timestamp=datetime.utcnow() - timedelta(days=1),
                device_id="device-1",
                user_id="user-1",
                tool_name="ChatGPT",
                tool_type="web",
                risk_level="green",
                prompt_length=100,
                detected_entity_types=[],
                entity_count=0,
                was_sanitized=False,
                log_metadata={"agent_version": "1.0.0"}
            ),
            LogEntryDB(
                timestamp=datetime.utcnow(),
                device_id="device-1",
                user_id="user-2",
                tool_name="Claude",
                tool_type="web",
                risk_level="red",
                prompt_length=200,
                detected_entity_types=["email", "person"],
                entity_count=2,
                was_sanitized=True,
                log_metadata={"agent_version": "1.0.0"}
            )
        ]
        session.add_all(logs)
        await session.commit()
    
    # Test without filters
    response = await client.get("/api/v1/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["logs"]) == 2
    
    # Test with risk level filter
    response = await client.get(
        "/api/v1/logs?risk_level=red",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["logs"][0]["riskLevel"] == "red"
    
    # Test with tool name filter
    response = await client.get(
        "/api/v1/logs?tool_name=ChatGPT",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["logs"][0]["toolName"] == "ChatGPT"


@pytest.mark.asyncio
async def test_get_logs_pagination(client, auth_headers):
    """Test log pagination"""
    # Insert multiple test logs
    async with TestSessionLocal() as session:
        logs = [
            LogEntryDB(
                timestamp=datetime.utcnow() - timedelta(hours=i),
                device_id="device-1",
                user_id=f"user-{i}",
                tool_name="ChatGPT",
                tool_type="web",
                risk_level="green",
                prompt_length=100,
                detected_entity_types=[],
                entity_count=0,
                was_sanitized=False,
                log_metadata={"agent_version": "1.0.0"}
            )
            for i in range(10)
        ]
        session.add_all(logs)
        await session.commit()
    
    # Test first page
    response = await client.get(
        "/api/v1/logs?page=1&limit=5",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 10
    assert len(data["logs"]) == 5
    assert data["page"] == 1
    assert data["totalPages"] == 2
    
    # Test second page
    response = await client.get(
        "/api/v1/logs?page=2&limit=5",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["logs"]) == 5
    assert data["page"] == 2


# Test summary stats endpoint
@pytest.mark.asyncio
async def test_get_summary_stats(client, auth_headers):
    """Test getting summary statistics"""
    # Insert test logs
    async with TestSessionLocal() as session:
        logs = [
            LogEntryDB(
                timestamp=datetime.utcnow(),
                device_id="device-1",
                user_id="user-1",
                tool_name="ChatGPT",
                tool_type="web",
                risk_level="green",
                prompt_length=100,
                detected_entity_types=[],
                entity_count=0,
                was_sanitized=False,
                log_metadata={"agent_version": "1.0.0"}
            ),
            LogEntryDB(
                timestamp=datetime.utcnow(),
                device_id="device-1",
                user_id="user-1",
                tool_name="Claude",
                tool_type="web",
                risk_level="red",
                prompt_length=200,
                detected_entity_types=["email"],
                entity_count=1,
                was_sanitized=True,
                log_metadata={"agent_version": "1.0.0"}
            ),
            LogEntryDB(
                timestamp=datetime.utcnow(),
                device_id="device-1",
                user_id="user-2",
                tool_name="ChatGPT",
                tool_type="web",
                risk_level="amber",
                prompt_length=150,
                detected_entity_types=["person"],
                entity_count=1,
                was_sanitized=False,
                log_metadata={"agent_version": "1.0.0"}
            )
        ]
        session.add_all(logs)
        await session.commit()
    
    response = await client.get(
        "/api/v1/logs/stats/summary",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["totalInteractions"] == 3
    assert data["riskDistribution"]["green"] == 1
    assert data["riskDistribution"]["amber"] == 1
    assert data["riskDistribution"]["red"] == 1
    assert len(data["topUsers"]) == 2
    assert len(data["topTools"]) == 2


# Test configuration endpoints
@pytest.mark.asyncio
async def test_create_config(client, auth_headers):
    """Test creating firewall configuration"""
    config_data = {
        "id": "config-1",
        "organizationId": "org-1",
        "monitoredTools": [
            {
                "toolName": "ChatGPT",
                "enabled": True,
                "toolType": "web"
            }
        ],
        "sensitivityThresholds": {
            "amberMinEntities": 1,
            "redMinEntities": 4,
            "highConfidenceThreshold": 0.9
        },
        "customPatterns": [],
        "logRetentionDays": 90,
        "updatedAt": datetime.utcnow().isoformat(),
        "updatedBy": "testuser"
    }
    
    response = await client.post(
        "/api/v1/config",
        json=config_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["organizationId"] == "org-1"
    assert data["logRetentionDays"] == 90


@pytest.mark.asyncio
async def test_get_config(client, auth_headers):
    """Test fetching firewall configuration"""
    # Create config first
    async with TestSessionLocal() as session:
        config = FirewallConfigDB(
            organization_id="org-1",
            monitored_tools=[{"tool_name": "ChatGPT", "enabled": True, "tool_type": "web"}],
            sensitivity_thresholds={"amber_min_entities": 1, "red_min_entities": 4, "high_confidence_threshold": 0.9},
            custom_patterns=[],
            log_retention_days=90,
            updated_by="testuser"
        )
        session.add(config)
        await session.commit()
    
    response = await client.get(
        "/api/v1/config?organization_id=org-1",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["organizationId"] == "org-1"


@pytest.mark.asyncio
async def test_update_config(client, auth_headers):
    """Test updating firewall configuration"""
    # Create config first
    async with TestSessionLocal() as session:
        config = FirewallConfigDB(
            organization_id="org-1",
            monitored_tools=[{"tool_name": "ChatGPT", "enabled": True, "tool_type": "web"}],
            sensitivity_thresholds={"amber_min_entities": 1, "red_min_entities": 4, "high_confidence_threshold": 0.9},
            custom_patterns=[],
            log_retention_days=90,
            updated_by="testuser"
        )
        session.add(config)
        await session.commit()
    
    # Update config
    update_data = {
        "id": "config-1",
        "organizationId": "org-1",
        "monitoredTools": [
            {
                "toolName": "ChatGPT",
                "enabled": False,
                "toolType": "web"
            }
        ],
        "sensitivityThresholds": {
            "amberMinEntities": 2,
            "redMinEntities": 5,
            "highConfidenceThreshold": 0.95
        },
        "customPatterns": [],
        "logRetentionDays": 120,
        "updatedAt": datetime.utcnow().isoformat(),
        "updatedBy": "testuser"
    }
    
    response = await client.put(
        "/api/v1/config",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["logRetentionDays"] == 120
    assert data["sensitivityThresholds"]["amberMinEntities"] == 2


@pytest.mark.asyncio
async def test_config_validation(client, auth_headers):
    """Test configuration validation"""
    # Test invalid retention days
    config_data = {
        "id": "config-1",
        "organizationId": "org-1",
        "monitoredTools": [],
        "sensitivityThresholds": {
            "amberMinEntities": 1,
            "redMinEntities": 4,
            "highConfidenceThreshold": 0.9
        },
        "customPatterns": [],
        "logRetentionDays": 20,  # Invalid: < 30
        "updatedAt": datetime.utcnow().isoformat(),
        "updatedBy": "testuser"
    }
    
    response = await client.post(
        "/api/v1/config",
        json=config_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "retention days" in response.json()["detail"].lower()


# Test export functionality
@pytest.mark.asyncio
async def test_export_logs_csv(client, auth_headers):
    """Test exporting logs in CSV format"""
    # Insert test log
    async with TestSessionLocal() as session:
        log = LogEntryDB(
            timestamp=datetime.utcnow(),
            device_id="device-1",
            user_id="user-1",
            tool_name="ChatGPT",
            tool_type="web",
            risk_level="green",
            prompt_length=100,
            detected_entity_types=[],
            entity_count=0,
            was_sanitized=False,
            log_metadata={"agent_version": "1.0.0"}
        )
        session.add(log)
        await session.commit()

    response = await client.get(
        "/api/v1/logs/export?format=csv",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    
    # Check CSV content
    content = response.text
    assert "id,timestamp,device_id" in content
    assert "device-1" in content


@pytest.mark.asyncio
async def test_export_logs_json(client, auth_headers):
    """Test exporting logs in JSON format"""
    # Insert test log
    async with TestSessionLocal() as session:
        log = LogEntryDB(
            timestamp=datetime.utcnow(),
            device_id="device-1",
            user_id="user-1",
            tool_name="ChatGPT",
            tool_type="web",
            risk_level="green",
            prompt_length=100,
            detected_entity_types=[],
            entity_count=0,
            was_sanitized=False,
            log_metadata={"agent_version": "1.0.0"}
        )
        session.add(log)
        await session.commit()

    response = await client.get(
        "/api/v1/logs/export?format=json",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]
    
    # Check JSON content
    import json
    content = json.loads(response.text)
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["device_id"] == "device-1"
