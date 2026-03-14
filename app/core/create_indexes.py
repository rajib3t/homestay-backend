import logging

logger = logging.getLogger(__name__)


class IndexCreator:
    """Utility to ensure MongoDB indexes for the application collections.

    Use `await IndexCreator.ensure_indexes(db)` at application startup.
    """

    @classmethod
    async def ensure_indexes(cls, db):
        try:
            # Countries: name (case-insensitive unique), code (unique)
            await db.countries.create_index(
                [("name", 1)],
                unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            await db.countries.create_index([("code", 1)], unique=True, background=True)

            # Cities: unique (name, country) with case-insensitive name, plus index on country
            await db.cities.create_index(
                [("name", 1), ("country", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            await db.cities.create_index([("country", 1)], background=True)

            # Locations: unique (name, city, country), plus index on city
            await db.locations.create_index(
                [("name", 1), ("city", 1), ("country", 1)], unique=True,
                collation={"locale": "en", "strength": 2},
                background=True,
            )
            await db.locations.create_index([("city", 1)], background=True)

            logger.info("Ensured MongoDB indexes for countries/cities/locations")

        except Exception:
            logger.exception("Failed to create/ensure MongoDB indexes")
            raise