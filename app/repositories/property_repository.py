from bson import ObjectId

from app.application.dto.property import PropertyQuery
from app.models.property_model import Property
from app.repositories.base_repository import BaseRepository
from app.repositories.builders.property_query_builder import PropertyQueryBuilder
from app.repositories.builders.property_pipeline_builder import PropertiesPipelineBuilder, PropertyPipelineBuilder


class PropertyRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db)
        self.collection_name = "properties"

    def collection(self):
        return getattr(self.db, self.collection_name)

    async def insert_one(self, data: Property, session=None):
        return await self.collection().insert_one(data, session=session)

    def find_many(self, query: dict, session=None):
        return self.collection().find(query, session=session)

    def list(self, query: dict, session=None):
        return self.find_many(query, session=session)

    async def count_documents(self, query: dict, session=None):
        return await self.collection().count_documents(query, session=session)

    def aggregate_properties(self, pipeline, session=None):
        return self.collection().aggregate(pipeline, session=session)


    async def get_property_by_id(self, property_id: str, session=None):
       
       try:
           object_id = ObjectId(property_id)
       except Exception:
           return None  
       
       data = await self.collection().find_one({"_id": object_id}, session=session)

       return data

    async def list_properties(self, query: PropertyQuery, session=None):
        self.validate_pagination(page=query.page, size=query.size)

        mongo_query = PropertyQueryBuilder.build(query.filters)
        pipeline = PropertiesPipelineBuilder.build(
            query=mongo_query,
            page=query.page,
            size=query.size,
            sort_by=query.sort_by,
            sort_order=query.sort_order,
        )

        cursor = self.aggregate_properties(pipeline, session=session)
        items = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            items.append(doc)

        total = await self.count_documents(mongo_query, session=session)

        return {
            "items": items,
            "total": total,
            "page": query.page,
            "size": query.size,
        }