# builders/city_pipeline_builder.py

class CityPipelineBuilder:

    @staticmethod
    def build(
        query,
        page,
        size,
        sort_by,
        sort_order,
    ):

        skip = (page - 1) * size

        sort_direction = (
            1 if sort_order.lower() == "asc" else -1
        )

        return [

            {
                "$match": query
            },

            {
                "$lookup": {
                    "from": "countries",
                    "localField": "country",
                    "foreignField": "_id",
                    "as": "country_doc"
                }
            },

            {
                "$unwind": {
                    "path": "$country_doc",
                    "preserveNullAndEmptyArrays": True
                }
            },

            {
                "$lookup": {
                    "from": "locations",
                    "localField": "_id",
                    "foreignField": "city",
                    "as": "locations"
                }
            },

            {
                "$addFields": {
                    "country": {
                        "$ifNull": [
                            "$country_doc.name",
                            ""
                        ]
                    },
                    "location_count": {
                        "$size": "$locations"
                    }
                }
            },

            {
                "$project": {
                    "country_doc": 0
                }
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
            }
        ]