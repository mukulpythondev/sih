import uuid
from django.conf import settings
from django.db import models

def generate_project_id():
    return str(uuid.uuid4())


class Project(models.Model):
    project_id = models.CharField(
        max_length=100,
        unique=True,
        default=generate_project_id,
        db_index=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="owned_projects",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="projects",
        help_text="Users allowed to view/query this project.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.project_id})"


class ChatSession(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("CLOSED", "Closed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chat_sessions",
    )

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="ACTIVE",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"ChatSession {self.id}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("USER", "User"),
        ("ASSISTANT", "Assistant"),
        ("SYSTEM", "System"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_messages",
        help_text="Null for system / assistant messages.",
    )

    content = models.TextField()

    # Optional meta (tokens, latency, model, etc.)
    metadata = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role} @ {self.created_at} in {self.session_id}"
