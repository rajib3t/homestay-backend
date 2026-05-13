from bson import ObjectId


class LocationQueryBuilder:

    @staticmethod
    async def build(filters: dict, repository):

        query = {}

        if not filters:
            return query

        for key, value in filters.items():

            if key == "country":

                if ObjectId.is_valid(value):
                    query["country"] = ObjectId(value)

                else:
                    countries = await repository.find_countries_by_name(value)

                    query["country"] = {
                        "$in": [c["_id"] for c in countries]
                    }

            elif key == "city":

                if ObjectId.is_valid(value):
                    query["city"] = ObjectId(value)

                else:
                    cities = await repository.find_locations_by_city_name(value)

                    query["city"] = {
                        "$in": [c["_id"] for c in cities]
                    }

            else:

                query[key] = {
                    "$regex": value,
                    "$options": "i",
                }

        return query