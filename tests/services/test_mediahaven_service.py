#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest.mock import patch, MagicMock

import pytest

from app.services.mediahaven_service import (
    MediahavenService,
    MediaObjectNotFoundException
)


class TestMediahavenService:

    @pytest.fixture
    @patch.object(
        MediahavenService,
        "_MediahavenService__get_token",
        return_value={"access_token": "Bear with me"},
    )
    def mediahaven_service(self, mhs_get_token_mock):
        mh_config_dict = {
            "environment": {
                "mediahaven": {
                    "host": "mediahaven",
                    "username": "user",
                    "password": "pass",
                }
            }
        }

        mhs = MediahavenService(mh_config_dict)
        # Patch out __get_token so it doesn't send a request to MediaHaven
        mhs._MediahavenService__get_token = mhs_get_token_mock
        return mhs

    @patch("app.services.mediahaven_service.requests")
    def test_get_fragment(self, get_media_mock, mediahaven_service):
        # Mock response data
        response_mock = MagicMock()
        response_mock.json.return_value = '{"key": "value"}'
        response_mock.status_code = 200
        get_media_mock.get.return_value = response_mock

        result = mediahaven_service.get_fragment("1")

        assert get_media_mock.get.call_count == 1
        assert get_media_mock.get.call_args[0][0] == "mediahaven/media/1"
        assert (
            get_media_mock.get.call_args[1]["headers"]["Authorization"]
            == "Bearer Bear with me"
        )
        assert (
            get_media_mock.get.call_args[1]["headers"]["Accept"]
            == "application/vnd.mediahaven.v2+json"
        )
        assert result == '{"key": "value"}'

    @patch("app.services.mediahaven_service.requests")
    def test_get_fragment_response_400(self, get_media_mock, mediahaven_service):
        # Construct response message
        status = 400
        code = "EPARAMINV"
        message = "No correct MediaObjectId or FragmentId specified"
        response = {
            "status": status,
            "message": message,
            "code": code,
        }

        # Mock response data
        response_mock = MagicMock()
        response_mock.json.return_value = response
        response_mock.status_code = status
        get_media_mock.get.return_value = response_mock

        with pytest.raises(MediaObjectNotFoundException) as error:
            mediahaven_service.get_fragment("1")
        assert error.value.args[0] == response

    @patch("app.services.mediahaven_service.requests")
    def test_get_fragment_response_404(self, get_media_mock, mediahaven_service):
        # Construct response message
        status = 404
        code = "EPARAMINV"
        fragment_id = "1"
        message = f"The object with fragmentId: {fragment_id} could not be found"
        response = {
            "status": status,
            "message": message,
            "code": code,
            "fragmentId": fragment_id,
        }

        # Mock response data
        response_mock = MagicMock()
        response_mock.json.return_value = response
        response_mock.status_code = status
        get_media_mock.get.return_value = response_mock

        with pytest.raises(MediaObjectNotFoundException) as error:
            mediahaven_service.get_fragment("1")
        assert error.value.args[0] == response
