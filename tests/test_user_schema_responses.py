from app.schemas.user_schema import LoginResponse, UserResponse


def test_login_response_accepts_embedded_user_payload():
    response = LoginResponse.model_validate(
        {
            "status": "success",
            "message": "Login successful",
            "data": {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "user": {
                    "id": "user-1",
                    "username": "rajib",
                    "email": "rajib.3t@gmail.com",
                    "user_type": "admin",
                    "first_name": "Rajib",
                    "last_name": "Mondal",
                    "mobile": "8282817714",
                    "created_at": "2026-03-14T20:28:04.563000",
                    "updated_at": "2026-04-01T17:56:41.040000",
                },
            },
        }
    )

    assert response.data.user.id == "user-1"
    assert response.data.user.email == "rajib.3t@gmail.com"


def test_user_response_wraps_single_user_payload():
    response = UserResponse.model_validate(
        {
            "status": "success",
            "message": "User",
            "data": {
                "_id": "user-1",
                "username": "rajib",
                "email": "rajib.3t@gmail.com",
                "user_type": "admin",
                "first_name": "Rajib",
                "last_name": "Mondal",
                "mobile": "8282817714",
            },
        }
    )

    assert response.data.id == "user-1"