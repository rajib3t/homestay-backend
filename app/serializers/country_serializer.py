# app/serializers/country_serializer.py

from bson import ObjectId


class CountrySerializer:

    @staticmethod
    def serialize(country: dict):

        return {

            "id": str(country["_id"]),

            "name": country.get("name"),

            "code": country.get("code"),

            "dial_code": country.get("dial_code", 1),

            "status": country.get("status"),

            "city_count": country.get("city_count", 0),

            "cities": [
                {
                    "id": str(city["_id"]),
                    "name": city.get("name"),
                    "country": str(city.get("country")),
                    "created_at": city.get("created_at"),
                    "updated_at": city.get("updated_at"),
                }
                for city in country.get("cities", [])
            ],

            "created_at": country.get("created_at"),
            "updated_at": country.get("updated_at"),
        }