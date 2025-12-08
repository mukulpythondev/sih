from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Project, ChatSession, ChatMessage

User = get_user_model()


class UserTinySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserTinySerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all(),
        required=False,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "owner",
            "members",
            "created_at",
            "updated_at",
            "is_archived",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]

    def create(self, validated_data):
        members = validated_data.pop("members", [])
        request = self.context.get("request")
        owner = request.user if request else None

        project = Project.objects.create(owner=owner, **validated_data)
        if members:
            project.members.set(members)
        # owner ko bhi member bna do by default
        if owner:
            project.members.add(owner)
        return project


class ChatSessionSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    created_by = UserTinySerializer(read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "project",
            "title",
            "created_by",
            "status",
            "created_at",
            "last_activity_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "last_activity_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        return ChatSession.objects.create(created_by=user, **validated_data)


class ChatMessageSerializer(serializers.ModelSerializer):
    session = serializers.PrimaryKeyRelatedField(queryset=ChatSession.objects.all())
    sender = UserTinySerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "session",
            "role",
            "sender",
            "content",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "sender", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None

        # USER role → sender = user
        # ASSISTANT / SYSTEM → sender = null
        role = validated_data.get("role", "USER").upper()
        if role == "USER":
            sender = user
        else:
            sender = None

        msg = ChatMessage.objects.create(sender=sender, **validated_data)

        # session ki last_activity update (safety)
        session = msg.session
        session.save(update_fields=["last_activity_at"])

        return msg
