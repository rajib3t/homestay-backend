from app.application.use_cases.setting.app_setting import AppSettingResponseBuilder
from app.application.use_cases.setting.image_service import BrandImageService


class FakeStorageService:
    def generate_presigned_url(self, key):
        return f"https://cdn.example.test/{key}"


def test_build_response_accepts_dict_values():
    builder = AppSettingResponseBuilder(BrandImageService(FakeStorageService()))

    result = builder.build_response({
        "app_logo": "brand/logo.png",
        "white_logo": "brand/white.png",
        "app_favicon": "brand/favicon.ico",
        "app_name": "StayHub",
    })

    assert result["app_logo"] == "https://cdn.example.test/brand/logo.png"
    assert result["white_logo"] == "https://cdn.example.test/brand/white.png"
    assert result["app_favicon"] == "https://cdn.example.test/brand/favicon.ico"
    assert result["app_name"] == "StayHub"


def test_build_response_skips_missing_image_fields():
    builder = AppSettingResponseBuilder(BrandImageService(FakeStorageService()))

    result = builder.build_response({"app_name": "StayHub"})

    assert result["app_name"] == "StayHub"
    assert "app_logo" not in result
