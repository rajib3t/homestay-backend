class LocationPipelineBuilder:

    @staticmethod
    def build(
        query: dict,
        page: int,
        size: int,
        sort_by: str,
        sort_order: str,
    ):

        skip = (page - 1) * size
        sort_direction = 1 if sort_order.lower() == "asc" else -1

        return [
            {"$match": query},

            {
                "$lookup": {
                    "from": "cities",
                    "localField": "city",
                    "foreignField": "_id",
                    "as": "city_doc",
                }
            },

            {
                "$unwind": {
                    "path": "$city_doc",
                    "preserveNullAndEmptyArrays": True,
                }
            },

            {
                "$lookup": {
                    "from": "countries",
                    "localField": "country",
                    "foreignField": "_id",
                    "as": "country_doc",
                }
            },

            {
                "$unwind": {
                    "path": "$country_doc",
                    "preserveNullAndEmptyArrays": True,
                }
            },

            {
                "$addFields": {
                    "city": {
                        "$ifNull": ["$city_doc.name", ""]
                    },
                    "country": {
                        "$ifNull": ["$country_doc.name", ""]
                    },
                }
            },

            {
                "$project": {
                    "city_doc": 0,
                    "country_doc": 0,
                }
            },

            {
                "$sort": {
                    sort_by: sort_direction
                }
            },

            {"$skip": skip},

            {"$limit": size},
        ]