import pytest

from app.application.use_cases.setting.coming_soon_use_case import PostComingSoonSettingUseCase


class FakeUploadFile:
    def __init__(self, filename: str, content_type: str, data: bytes):
        self.filename = filename
        self.content_type = content_type
        self._data = data

    async def read(self):
        return self._data


class FakeStorageService:
    def __init__(self):
        self.uploads = []
        self.deleted = []

    async def upload_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        self.uploads.append((key, data, content_type))
        return key

    async def delete_object(self, key: str) -> bool:
        self.deleted.append(key)
        return True


class FakeComingSoonService:
    def __init__(self, existing=None):
        self.saved = []
        self.existing = existing or {}

    async def save(self, data: dict, session=None):
        self.saved.append(data)
        return data

    async def get(self, session=None):
        return self.existing


@pytest.mark.asyncio
async def test_post_coming_soon_use_case_uploads_files_before_saving():
    service = FakeComingSoonService()
    storage = FakeStorageService()
    use_case = PostComingSoonSettingUseCase(service, storage, current_user=None, uow=None)

    result = await use_case.execute(
        {
            "background_image_url": FakeUploadFile("bg.png", "image/png", b"image-bytes"),
            "video_url": FakeUploadFile("intro.mp4", "video/mp4", b"video-bytes"),
            "launch_date": "2026-07-17",
        }
    )

    assert len(storage.uploads) == 2
    assert service.saved[0]["background_image_url"].startswith("coming-soon/images/background_image_url_")
    assert service.saved[0]["video_url"].startswith("coming-soon/videos/video_url_")
    assert result["launch_date"] == "2026-07-17"


@pytest.mark.asyncio
async def test_post_coming_soon_use_case_deletes_replaced_files():
    service = FakeComingSoonService(
        existing={
            "background_image_url": "old/background.png",
            "video_url": "old/intro.mp4",
        }
    )
    storage = FakeStorageService()
    use_case = PostComingSoonSettingUseCase(service, storage, current_user=None, uow=None)

    await use_case.execute(
        {
            "background_image_url": FakeUploadFile("bg.png", "image/png", b"image-bytes"),
            "video_url": FakeUploadFile("intro.mp4", "video/mp4", b"video-bytes"),
            "launch_date": "2026-07-17",
        }
    )

    assert storage.deleted == ["old/background.png", "old/intro.mp4"]
