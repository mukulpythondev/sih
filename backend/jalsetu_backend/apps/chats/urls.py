from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ProjectViewSet,
    ChatSessionViewSet,
    ChatMessageViewSet,
    ProjectCreateView,
    DocumentUploadView,
    QueryView,
)


router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"chat-sessions", ChatSessionViewSet, basename="chat-session")
router.register(r"chat-messages", ChatMessageViewSet, basename="chat-message")

urlpatterns = router.urls + [
    path("project/create/", ProjectCreateView.as_view(), name="project-create"),
    path("document/upload/", DocumentUploadView.as_view(), name="document-upload"),
    path("query/", QueryView.as_view(), name="query"),
]
