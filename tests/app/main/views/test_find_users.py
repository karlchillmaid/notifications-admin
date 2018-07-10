import pytest
from flask import url_for
from lxml import html
from app.main.views.find_users import find_users_by_email

from tests import user_json
from tests.conftest import mock_get_user
from app.notify_client.user_api_client import User

def test_find_users_by_email_page_loads_correctly(
    client,
    platform_admin_user,
    mocker
):
    mock_get_user(mocker, user=platform_admin_user)
    client.login(platform_admin_user)
    response = client.get(url_for('main.find_users_by_email'))
    assert response.status_code == 200

    document = html.fromstring(response.get_data(as_text=True))
    header = document.xpath('//h1')[0].text
    assert "Find users by e-mail" in header
    assert len(document.xpath("//input[@type='search']")) > 0


def test_find_users_by_email_displays_users_found(
    client,
    platform_admin_user,
    mocker
):
    mock_get_user(mocker, user=platform_admin_user)
    client.login(platform_admin_user)
    mocker.patch('app.user_api_client.find_users_by_full_or_partial_email', return_value={"data": [user_json()]}, autospec=True)
    response = client.post(url_for('main.find_users_by_email'), data={"search": "twilight.sparkle"})
    assert response.status_code == 200

    document = html.fromstring(response.get_data(as_text=True))
    assert "Test User" in document.text_content()


def test_find_users_by_email_displays_multiple_users(
    client,
    platform_admin_user,
    mocker
):
    mock_get_user(mocker, user=platform_admin_user)
    client.login(platform_admin_user)
    mocker.patch('app.user_api_client.find_users_by_full_or_partial_email', return_value={"data": [
        user_json(name="Apple Jack"),
        user_json(name="Apple Bloom")
    ]}, autospec=True)
    response = client.post(url_for('main.find_users_by_email'), data={"search": "apple"})
    assert response.status_code == 200

    document = html.fromstring(response.get_data(as_text=True))
    assert "Apple Jack" in document.text_content()
    assert "Apple Bloom" in document.text_content()


def test_find_users_by_email_displays_message_if_no_users_found(
    client,
    platform_admin_user,
    mocker
):
    mock_get_user(mocker, user=platform_admin_user)
    client.login(platform_admin_user)
    mocker.patch('app.user_api_client.find_users_by_full_or_partial_email', return_value={"data": []}, autospec=True)
    response = client.post(url_for('main.find_users_by_email'), data={"search": "twilight.sparkle"})
    assert response.status_code == 200

    document = html.fromstring(response.get_data(as_text=True))
    assert "No users found." in document.text_content()


def test_find_users_by_email_validates_against_empty_search_submission(
    client,
    platform_admin_user,
    mocker
):
    mock_get_user(mocker, user=platform_admin_user)
    client.login(platform_admin_user)
    response = client.post(url_for('main.find_users_by_email'), data={"search": ""})
    assert response.status_code == 400

    document = html.fromstring(response.get_data(as_text=True))
    assert "You need to enter full or partial e-mail address to search by." in document.text_content()


def test_user_information_page_shows_information_about_user(
    client,
    platform_admin_user,
    mocker
):
    mocker.patch('app.user_api_client.get_user', side_effect=[
        platform_admin_user,
        User(user_json(name="Apple Bloom"))
    ], autospec=True)
    client.login(platform_admin_user)
    response = client.get(url_for('main.user_information', user_id=345))
    assert response.status_code == 200

    document = html.fromstring(response.get_data(as_text=True))
    header = document.xpath('//h1')[0].text
    assert "Apple Bloom" in header
