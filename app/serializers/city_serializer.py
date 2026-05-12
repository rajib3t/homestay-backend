class CitySerializer:

    @staticmethod
    def serialize(doc):

        if not doc:
            return None

        doc["id"] = str(doc.pop("_id"))

        # MAIN CITY COUNTRY
        if doc.get("country"):
            doc["country"] = str(doc["country"])

        # NESTED LOCATIONS
        for loc in doc.get("locations", []):

            loc["id"] = str(loc.pop("_id"))

            if loc.get("city"):
                loc["city"] = str(loc["city"])

            if loc.get("country"):
                loc["country"] = str(loc["country"])

        return doc