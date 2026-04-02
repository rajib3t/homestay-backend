import logging

logger = logging.getLogger(__name__)


class IndexCreator:
    """Utility to ensure MongoDB indexes for the application collections.

    Use `await IndexCreator.ensure_indexes(db)` at application startup.
    """

    @staticmethod
    def _normalize_keys(keys):
        return list(keys)

    @staticmethod
    def _normalize_existing_keys(existing_key):
        if isinstance(existing_key, dict):
            return list(existing_key.items())
        return list(existing_key)

    @classmethod
    async def _ensure_index(cls, collection, keys, *, name=None, **options):
        index_name = name
        existing_indexes = await collection.index_information()

        if index_name and index_name in existing_indexes:
            existing_index = existing_indexes[index_name]
            existing_keys = cls._normalize_existing_keys(existing_index.get("key", []))
            requested_keys = cls._normalize_keys(keys)

            if existing_keys != requested_keys:
                logger.warning(
                    "Skipping index creation for %s.%s because an index with the same name already exists with different keys",
                    collection.name,
                    index_name,
                )
                return index_name

            conflicts = []
            for option_name, option_value in options.items():
                if existing_index.get(option_name) != option_value:
                    conflicts.append(
                        f"{option_name}: existing={existing_index.get(option_name)!r}, requested={option_value!r}"
                    )

            if conflicts:
                logger.warning(
                    "Skipping index creation for %s.%s because an index with the same name already exists with different options: %s",
                    collection.name,
                    index_name,
                    "; ".join(conflicts),
                )
                return index_name

            logger.debug("Index %s already exists on %s", index_name, collection.name)
            return index_name

        return await collection.create_index(keys, name=name, **options)

    @classmethod
    async def ensure_indexes(cls, db):
        try:
            await cls._ensure_index(
                db.users,
                [("email", 1)], unique=True,
                name="email_1",
                sparse=True,
            )
            await cls._ensure_index(
                db.users,
                [("username", 1)], unique=True,
                name="username_1",
                sparse=True,
                background=True,
            )
            await cls._ensure_index(
                db.users,
                [("mobile", 1)], unique=True,
                name="mobile_1",
                sparse=True,
                background=True,
                collation={"locale": "en", "strength": 2},
               
            )
            # Countries: name (case-insensitive unique), code (unique)
            await cls._ensure_index(
                db.countries,
                [("name", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            await cls._ensure_index(db.countries, [("code", 1)], unique=True, background=True)

            # Cities: unique (name, country) with case-insensitive name, plus index on country
            await cls._ensure_index(
                db.cities,
                [("name", 1), ("country", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            await cls._ensure_index(db.cities, [("country", 1)], background=True)

            # Locations: unique (name, city, country), plus index on city
            await cls._ensure_index(
                db.locations,
                [("name", 1), ("city", 1), ("country", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            await cls._ensure_index(db.locations, [("city", 1)], background=True)

            

            await cls._ensure_index(
                db.amenities,
                [("name", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            logger.info("Ensured MongoDB indexes for amenities")
            await cls._ensure_index(
                db.facilities,
                [("name", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            logger.info("Ensured MongoDB indexes for facilities")
            await cls._ensure_index(
                db.room_types,
                [("name", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            logger.info("Ensured MongoDB indexes for room types")
        except Exception:
            logger.exception("Failed to create/ensure MongoDB indexes")
            raise