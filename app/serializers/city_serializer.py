# serializers/city_serializer.py

class CitySerializer:

    @staticmethod
    def serialize(doc):

        doc["id"] = str(doc.pop("_id"))

        for loc in doc.get("locations", []):

            loc["id"] = str(loc.pop("_id"))

            if loc.get("city"):
                loc["city"] = str(loc["city"])

            if loc.get("country"):
                loc["country"] = str(loc["country"])

        return doc