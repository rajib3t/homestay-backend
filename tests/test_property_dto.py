from app.application.dto.property import Amenity, PropertyDTO


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
