# builders/city_query_builder.py

from bson import ObjectId


class CityQueryBuilder:

    @staticmethod
    async def build(filters, repository=None):

        query = {}

        if not filters:
            return query

        for key, value in filters.items():

            if value is None:
                continue

            if key == "country":

                if ObjectId.is_valid(value):

                    query["country"] = ObjectId(value)

                else:

                    countries = await repository.find_countries_by_name(
                        value
                    )

                    query["country"] = {
                        "$in": [c["_id"] for c in countries]
                    }

            elif isinstance(value, str):

                query[key] = {
                    "$regex": value,
                    "$options": "i",
                }

            else:

                query[key] = value

        return query