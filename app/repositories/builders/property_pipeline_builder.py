from bson import ObjectId


class PropertiesPipelineBuilder:

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

            # Convert string IDs to ObjectId for lookups
            {
                "$addFields": {
                    "city_id": {"$toObjectId": "$city"},
                    "country_id": {"$toObjectId": "$country"},
                    "location_id": {"$toObjectId": "$location"},
                    "amenity_ids": {
                        "$map": {
                            "input": {"$ifNull": ["$amenities", []]},
                            "as": "amenity",
                            "in": {"$toObjectId": "$$amenity.name"}
                        }
                    },
                    "facility_ids": {
                        "$map": {
                            "input": {"$ifNull": ["$facilities", []]},
                            "as": "facility",
                            "in": {"$toObjectId": "$$facility.name"}
                        }
                    }
                }
            },

            # Lookup city
            {
                "$lookup": {
                    "from": "cities",
                    "localField": "city_id",
                    "foreignField": "_id",
                    "as": "city_doc"
                }
            },

            {
                "$unwind": {
                    "path": "$city_doc",
                    "preserveNullAndEmptyArrays": True
                }
            },

            # Lookup country
            {
                "$lookup": {
                    "from": "countries",
                    "localField": "country_id",
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

            # Lookup location
            {
                "$lookup": {
                    "from": "locations",
                    "localField": "location_id",
                    "foreignField": "_id",
                    "as": "location_doc"
                }
            },

            {
                "$unwind": {
                    "path": "$location_doc",
                    "preserveNullAndEmptyArrays": True
                }
            },

            # Lookup amenities
            {
                "$lookup": {
                    "from": "amenities",
                    "localField": "amenity_ids",
                    "foreignField": "_id",
                    "as": "amenity_docs"
                }
            },

            # Lookup facilities
            {
                "$lookup": {
                    "from": "facilities",
                    "localField": "facility_ids",
                    "foreignField": "_id",
                    "as": "facility_docs"
                }
            },

            # Add fields with resolved names for city, country, location
            {
                "$addFields": {
                    "city_name": {
                        "$ifNull": ["$city_doc.name", ""]
                    },
                    "country_name": {
                        "$ifNull": ["$country_doc.name", ""]
                    },
                    "location_name": {
                        "$ifNull": ["$location_doc.name", ""]
                    },
                    "amenities": {
                        "$map": {
                            "input": "$amenities",
                            "as": "amenity",
                            "in": {
                                "name": {
                                    "$let": {
                                        "vars": {
                                            "doc": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$amenity_docs",
                                                            "cond": {"$eq": ["$$this._id", {"$toObjectId": "$$amenity.name"}]}
                                                        }
                                                    },
                                                    0
                                                ]
                                            }
                                        },
                                        "in": {"$ifNull": ["$$doc.name", "$$amenity.name"]}
                                    }
                                },
                                "allow": "$$amenity.allow"
                            }
                        }
                    },
                    "facilities": {
                        "$map": {
                            "input": "$facilities",
                            "as": "facility",
                            "in": {
                                "name": {
                                    "$let": {
                                        "vars": {
                                            "doc": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$facility_docs",
                                                            "cond": {"$eq": ["$$this._id", {"$toObjectId": "$$facility.name"}]}
                                                        }
                                                    },
                                                    0
                                                ]
                                            }
                                        },
                                        "in": {"$ifNull": ["$$doc.name", "$$facility.name"]}
                                    }
                                },
                                "allow": "$$facility.allow"
                            }
                        }
                    }
                }
            },

            # Project to remove temporary fields
            {
                "$project": {
                    "city_doc": 0,
                    "country_doc": 0,
                    "location_doc": 0,
                    "amenity_docs": 0,
                    "facility_docs": 0,
                    "city_id": 0,
                    "country_id": 0,
                    "location_id": 0,
                    "amenity_ids": 0,
                    "facility_ids": 0
                }
            },

            {
                "$sort": {
                    sort_by: sort_direction
                }
            },

            {"$skip": skip},

            {"$limit": size}
        ]


class PropertyPipelineBuilder:
    @staticmethod
    def build(property_id: str):
        object_id = ObjectId(property_id)

        return [
            {"$match": {"_id": object_id}},
            {
                "$addFields": {
                    "city_id": {"$toObjectId": "$city"},
                    "country_id": {"$toObjectId": "$country"},
                    "location_id": {"$toObjectId": "$location"},
                    "amenity_ids": {
                        "$map": {
                            "input": {"$ifNull": ["$amenities", []]},
                            "as": "amenity",
                            "in": {"$toObjectId": "$$amenity.name"},
                        }
                    },
                    "facility_ids": {
                        "$map": {
                            "input": {"$ifNull": ["$facilities", []]},
                            "as": "facility",
                            "in": {"$toObjectId": "$$facility.name"},
                        }
                    },
                }
            },
            {
                "$lookup": {
                    "from": "cities",
                    "localField": "city_id",
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
                    "localField": "country_id",
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
                "$lookup": {
                    "from": "locations",
                    "localField": "location_id",
                    "foreignField": "_id",
                    "as": "location_doc",
                }
            },
            {
                "$unwind": {
                    "path": "$location_doc",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$lookup": {
                    "from": "amenities",
                    "localField": "amenity_ids",
                    "foreignField": "_id",
                    "as": "amenity_docs",
                }
            },
            {
                "$lookup": {
                    "from": "facilities",
                    "localField": "facility_ids",
                    "foreignField": "_id",
                    "as": "facility_docs",
                }
            },
            {
                "$addFields": {
                    "city_name": {"$ifNull": ["$city_doc.name", ""]},
                    "country_name": {"$ifNull": ["$country_doc.name", ""]},
                    "location_name": {"$ifNull": ["$location_doc.name", ""]},
                    "amenities": {
                        "$map": {
                            "input": "$amenities",
                            "as": "amenity",
                            "in": {
                                "name": {
                                    "$let": {
                                        "vars": {
                                            "doc": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$amenity_docs",
                                                            "cond": {
                                                                "$eq": [
                                                                    "$$this._id",
                                                                    {"$toObjectId": "$$amenity.name"},
                                                                ]
                                                            },
                                                        }
                                                    },
                                                    0,
                                                ]
                                            }
                                        },
                                        "in": {"$ifNull": ["$$doc.name", "$$amenity.name"]},
                                    }
                                },
                                "allow": "$$amenity.allow",
                            },
                        }
                    },
                    "facilities": {
                        "$map": {
                            "input": "$facilities",
                            "as": "facility",
                            "in": {
                                "name": {
                                    "$let": {
                                        "vars": {
                                            "doc": {
                                                "$arrayElemAt": [
                                                    {
                                                        "$filter": {
                                                            "input": "$facility_docs",
                                                            "cond": {
                                                                "$eq": [
                                                                    "$$this._id",
                                                                    {"$toObjectId": "$$facility.name"},
                                                                ]
                                                            },
                                                        }
                                                    },
                                                    0,
                                                ]
                                            }
                                        },
                                        "in": {"$ifNull": ["$$doc.name", "$$facility.name"]},
                                    }
                                },
                                "allow": "$$facility.allow",
                            },
                        }
                    },
                }
            },
            {
                "$project": {
                    "city_doc": 0,
                    "country_doc": 0,
                    "location_doc": 0,
                    "amenity_docs": 0,
                    "facility_docs": 0,
                    "city_id": 0,
                    "country_id": 0,
                    "location_id": 0,
                    "amenity_ids": 0,
                    "facility_ids": 0,
                }
            },
            {"$limit": 1},
        ]
