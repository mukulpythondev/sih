import requests
from rest_framework import viewsets, permissions, status
from .models import Project, ChatSession, ChatMessage
from .serializers import (
    ProjectSerializer,
    ChatSessionSerializer,
    ChatMessageSerializer,
)
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Project


FASTAPI_URL = getattr(settings, "FASTAPI_URL", "").rstrip("/")


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        name = request.data.get("name")
        if not name:
            return Response(
                {"detail": "Field 'name' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = Project.objects.create(name=name)
        data = {
            "project_id": project.project_id,
            "status": "created",
        }
        return Response(data, status=status.HTTP_201_CREATED)


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        if not FASTAPI_URL:
            return Response(
                {"detail": "FASTAPI_URL not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        project_id = request.data.get("project_id")
        file_obj = request.FILES.get("file")

        if not project_id:
            return Response(
                {"detail": "Field 'project_id' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not file_obj:
            return Response(
                {"detail": "Field 'file' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # (Optional) validate ki yeh project exist karta hai
        if not Project.objects.filter(project_id=project_id).exists():
            return Response(
                {"detail": "Invalid project_id."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            files = {
                "file": (
                    file_obj.name,
                    file_obj.read(),
                    getattr(file_obj, "content_type", "application/octet-stream"),
                )
            }
            data = {"project_id": project_id}

            resp = requests.post(
                f"{FASTAPI_URL}/upload",
                data=data,
                files=files,
                timeout=60,
            )
        except requests.RequestException as e:
            return Response(
                {"detail": f"Error contacting RAG service: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        try:
            json_data = resp.json()
        except ValueError:
            return Response(
                {
                    "detail": "Invalid response from RAG service.",
                    "status_code_from_rag": resp.status_code,
                    "raw": resp.text[:500],
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(json_data, status=resp.status_code)


class QueryView(APIView):
    """
    POST /api/query/

    Desktop → Django:
    {
      "project_id": "9f8a213d-23as-98sa",
      "query": "Summaries mentioned in page 3?"
    }

    Django → FastAPI: same body on /query

    FastAPI Response:
    {
      "answer": "...",
      "citations": [...],
      "processing_time": 4.35
    }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not FASTAPI_URL:
            return Response(
                {"detail": "FASTAPI_URL not configured."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        project_id = request.data.get("project_id")
        query = request.data.get("query")

        if not project_id or not query:
            return Response(
                {"detail": "Fields 'project_id' and 'query' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # (Optional) validate project_id locally
        if not Project.objects.filter(project_id=project_id).exists():
            return Response(
                {"detail": "Invalid project_id."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payload = {
            "project_id": project_id,
            "query": query,
        }

        try:
            resp = requests.post(
                f"{FASTAPI_URL}/query",
                json=payload,
                timeout=60,
            )
        except requests.RequestException as e:
            return Response(
                {"detail": f"Error contacting RAG service: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            json_data = resp.json()
        except ValueError:
            return Response(
                {
                    "detail": "Invalid response from RAG service.",
                    "status_code_from_rag": resp.status_code,
                    "raw": resp.text[:500],
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(json_data, status=resp.status_code)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Only for the enrolled team
        return Project.objects.filter(members=user).distinct()


class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatSession.objects.filter(project__members=user).select_related("project")


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatMessage.objects.filter(
            session__project__members=user
        ).select_related("session", "session__project")
