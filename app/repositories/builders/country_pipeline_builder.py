# app/repositories/builders/country_pipeline_builder.py

class CountryPipelineBuilder:

    @staticmethod
    def build(
        *,
        query: dict,
        page: int,
        size: int,
        sort_by: str,
        sort_order: str,
    ):

        skip = (page - 1) * size

        sort_direction = 1 if sort_order == "asc" else -1

        return [

            {
                "$match": query
            },

            {
                "$sort": {
                    sort_by: sort_direction
                }
            },

            {
                "$skip": skip
            },

            {
                "$limit": size
            },

            {
                "$lookup": {
                    "from": "cities",
                    "localField": "_id",
                    "foreignField": "country",
                    "as": "cities"
                }
            },

            {
                "$addFields": {
                    "city_count": {
                        "$size": "$cities"
                    }
                }
            }
        ]