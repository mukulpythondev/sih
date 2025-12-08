import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def super_admin_user(django_user_model):
    user = django_user_model.objects.create_user(
        username="superadmin",
        email="superadmin@example.com",
        password="superpass123",
        role="SUPER_ADMIN",
        first_name="Super",
        last_name="Admin",
    )
    return user


@pytest.fixture
def junior_analyst_user(django_user_model):
    user = django_user_model.objects.create_user(
        username="junior1",
        email="junior@example.com",
        password="juniorpass123",
        role="JUNIOR_ANALYST",
    )
    return user


def get_tokens_for_user(client: APIClient, username: str, password: str):
    url = reverse("accounts:token_obtain_pair")
    response = client.post(
        url,
        {"username": username, "password": password},
        format="json",
    )
    return response


def test_login_success_for_super_admin(api_client, super_admin_user):
    response = get_tokens_for_user(api_client, "superadmin", "superpass123")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access" in data and "refresh" in data
    assert data["user"]["role"] == "SUPER_ADMIN"


def test_login_failure_wrong_password(api_client, super_admin_user):
    response = get_tokens_for_user(api_client, "superadmin", "wrongpass")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_requires_authentication(api_client):
    url = reverse("accounts:me")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_returns_current_user(api_client, super_admin_user):
    login_response = get_tokens_for_user(api_client, "superadmin", "superpass123")
    access = login_response.json()["access"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    url = reverse("accounts:me")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == "superadmin"
    assert data["role"] == "SUPER_ADMIN"


def test_token_refresh(api_client, super_admin_user):
    login_response = get_tokens_for_user(api_client, "superadmin", "superpass123")
    refresh = login_response.json()["refresh"]

    url = reverse("accounts:token_refresh")
    response = api_client.post(url, {"refresh": refresh}, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.json()
