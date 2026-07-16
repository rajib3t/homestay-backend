from bson import ObjectId
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.application.dto.property import Amenity, PropertyDTO, PropertyQuery
from app.repositories.builders.property_pipeline_builder import PropertyPipelineBuilder


def test_property_dto_can_be_instantiated_with_required_fields():
    dto = PropertyDTO(
        name="Ocean View",
        vendor="vendor-1",
        location="Dhaka",
        city="Dhaka",
        country="Bangladesh",
        address="123 Main Street",
        longitude=90.4125,
        latitude=23.8103,
        amenities=[Amenity(name="wifi")],
    )

    assert dto.name == "Ocean View"
    assert dto.vendor == "vendor-1"
    assert dto.location == "Dhaka"
    assert dto.amenities[0].name == "wifi"


def test_property_query_depends_accepts_missing_filters_from_query_params():
    app = FastAPI()

    @app.get("/properties")
    async def route(params: PropertyQuery = Depends()):
        return params.model_dump()

    client = TestClient(app)
    response = client.get("/properties?page=1&size=5")

    assert response.status_code == 200
    assert response.json()["page"] == 1
    assert response.json()["size"] == 5
    assert response.json()["filters"] == {}


def test_property_pipeline_builder_builds_single_property_pipeline():
    property_id = str(ObjectId())

    pipeline = PropertyPipelineBuilder.build(property_id=property_id)

    assert pipeline[0] == {"$match": {"_id": ObjectId(property_id)}}
    assert pipeline[-1] == {"$limit": 1}
