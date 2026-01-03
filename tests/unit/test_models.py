import uuid

from api.v1.models.user import User
from api.v1.models.project import Project
from api.v1.models.pdf import PDF, PDFStatus
from api.v1.models.chat import ChatSession, ChatMessage, MessageRole


class TestUserModel:
    """Test User model."""

    def test_user_creation(self):
        """Test user model creation."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashedpass",
            is_active=True,
        )

        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashedpass"
        assert user.is_active is True

    def test_user_defaults(self):
        """Test user model defaults."""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashedpass",
            is_active=True,
        )

        # Should have UUID assigned
        assert isinstance(user.id, uuid.UUID)
        assert user.id == user_id
        # Should be active by default
        assert user.is_active is True


class TestProjectModel:
    """Test Project model."""

    def test_project_creation(self):
        """Test project model creation."""
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()

        project = Project(
            id=project_id,
            name="Test Project",
            description="A test project",
            owner_user_id=user_id,
        )

        assert project.id == project_id
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.owner_user_id == user_id

    def test_project_minimal(self):
        """Test project with minimal required fields."""
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()

        project = Project(id=project_id, name="Minimal Project", owner_user_id=user_id)

        assert isinstance(project.id, uuid.UUID)
        assert project.id == project_id
        assert project.name == "Minimal Project"
        assert project.description is None
        assert project.owner_user_id == user_id


class TestPDFModel:
    """Test PDF model."""

    def test_pdf_creation(self):
        """Test PDF model creation."""
        pdf_id = uuid.uuid4()
        project_id = uuid.uuid4()

        pdf = PDF(
            id=pdf_id,
            filename="test.pdf",
            storage_path="/storage/test.pdf",
            status=PDFStatus.UPLOADED,
            project_id=project_id,
        )

        assert pdf.id == pdf_id
        assert pdf.filename == "test.pdf"
        assert pdf.storage_path == "/storage/test.pdf"
        assert pdf.project_id == project_id
        assert pdf.status == PDFStatus.UPLOADED

    def test_pdf_status_enum(self):
        """Test PDF status enumeration."""
        project_id = uuid.uuid4()

        pdf = PDF(
            filename="test.pdf",
            storage_path="/storage/test.pdf",
            project_id=project_id,
            status=PDFStatus.INDEXED,
        )

        assert pdf.status == PDFStatus.INDEXED
        assert pdf.status.value == "INDEXED"


class TestChatModels:
    """Test Chat models."""

    def test_chat_session_creation(self):
        """Test ChatSession model creation."""
        session_id = uuid.uuid4()
        project_id = uuid.uuid4()

        session = ChatSession(id=session_id, project_id=project_id)

        assert session.id == session_id
        assert session.project_id == project_id

    def test_chat_message_creation(self):
        """Test ChatMessage model creation."""
        message_id = uuid.uuid4()
        session_id = uuid.uuid4()

        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            role=MessageRole.USER,
            content="Hello, how are you?",
        )

        assert message.id == message_id
        assert message.session_id == session_id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, how are you?"

    def test_message_role_enum(self):
        """Test MessageRole enumeration."""
        session_id = uuid.uuid4()

        user_message = ChatMessage(
            session_id=session_id, role=MessageRole.USER, content="User message"
        )

        assistant_message = ChatMessage(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content="Assistant message",
        )

        assert user_message.role == MessageRole.USER
        assert user_message.role.value == "user"
        assert assistant_message.role == MessageRole.ASSISTANT
        assert assistant_message.role.value == "assistant"
