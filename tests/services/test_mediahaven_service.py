from unittest.mock import patch, MagicMock

from app.services.mediahaven_service import MediahavenService


class TestMediahavenService:
    @patch("app.services.mediahaven_service.requests")
    @patch.object(
        MediahavenService,
        "_MediahavenService__get_token",
        return_value={"access_token": "Bear with me"},
    )
    def test_get_fragment(self, mhs_get_token_mock, get_media_mock):
        mh_config_dict = {
            "environment": {
                "mediahaven": {
                    "host": "mediahaven",
                    "username": "user",
                    "password": "pass",
                }
            }
        }

        # Mock response data
        response_mock = MagicMock()
        response_mock.json.return_value = '{"key": "value"}'
        response_mock.status_code = 200
        get_media_mock.get.return_value = response_mock

        mhs = MediahavenService(mh_config_dict)
        mhs.get_fragment("1")

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
