# drf-pretty-update

Simple HTTP POST, PUT & PATCH request handler for Django REST Framework(DRF) nested data

## Getting Started
drf-pretty-update has two components, Serializer and Fields. The Serializer which is `NestedModelSerializer` has `update` and `create` logics for nested fields, Fields are used to validate data before dispatching update or create.

There are two types of fields which are `ReplaceableNestedField` and `WritableNestedField`.

`ReplaceableNestedField:` is used if you want to update nested field by using ids of existing data(basically associate and dessociate existing nested resources with the parent resource without actually mutating the nested resource).

`WritableNestedField:` is used if you want to be able to actually mutate(create and update) nested resources.

### Using ReplaceableNestedField
```python
from app.models import Location, Amenity, Property
from drf_pretty_update import NestedModelSerializer, ReplaceableNestedField, WritableNestedField

class LocationSerializer(NestedModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "city", "country")


class AmenitySerializer(NestedModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name")


class PropertySerializer(NestedModelSerializer):
    location = ReplaceableNestedField(serializer=LocationSerializer)
    amenities = ReplaceableNestedField(serializer=AmenitySerializer ,many=True)
    class Meta:
        model = Property
        fields = (
            'id', 'price', 'location', 'amenities'
        )
```
<br>


```POST /api/property/```

Request Body
```json
{
    "price": 40000,
    "location": 2,
    "amenities": [1,2,3]
}
```
Note: Here location resource with id 2 and amenities with ids 1,2 and 3 are already existing, so what's done here is create new property resource and associate it with such location and amenities.
<br>

Response
```json
{
    "id": 1,
    "price": 40000,
    "location": {
        "id": 2,
        "city": "Tokyo",
        "country": "China"
    },
    "amenities": [
        {"id": 1, "name": "Water"},
        {"id": 2, "name": "Electricity"},
        {"id": 3, "name": "Swimming Pool"}
    ]
}
```
<br>


```PUT /api/property/1/```

Request Body

```json
{
    "price": 35000,
    "location": 2,
    "amenities": {
        "add": [4,5],
        "remove": [1, 3]
    }
}
```
What's done here is associate amenities with ids 4 and 5 with the property being updated and then dessociate amenities with ids 1 and 3(remove them from a list of amenities of a property being updated).

<br>

Response
```json
{
    "price": 35000,
    "location": {
        "id": 2,
        "city": "Tokyo",
        "country": "China"
    },
    "amenities": [
        {"id": 2, "name": "Electricity"},
        {"id": 4, "name": "Back yard"},
        {"id": 5, "name": "Fance"},
    ]
}
```

<br>
<br>

### Using WritableNestedField
```python
from app.models import Location, Amenity, Property
from drf_pretty_update import NestedModelSerializer, ReplaceableNestedField, WritableNestedField

class LocationSerializer(NestedModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "city", "country")


class AmenitySerializer(NestedModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name")
        

class PropertySerializer(NestedModelSerializer):
    location = WritableNestedField(serializer=LocationSerializer)
    amenities = WritableNestedField(serializer=AmenitySerializer ,many=True)
    class Meta:
        model = Property
        fields = (
            'id', 'price', 'location', 'amenities'
        )
```
<br>


```POST /api/property/```

Request Body
```json
{
    "price": 60000,
    "location": {
        "city": "Newyork",
        "country": "USA"
    },
    "amenities": [
        {"name": "Water"},
        {"name": "Electricity"},
        {"name": "Swimming Pool"}
    ]
}
```
What's done here is pretty clear that location and amenities will be created and associated with the property resource being created.

<br>

Response
```json
{
    "id": 2,
    "price": 60000,
    "location": {
        "id": 3,
        "city": "Newyork",
        "country": "USA"
    },
    "amenities": [
        {"id": 1, "name": "Watererr"},
        {"id": 2, "name": "Electricity"},
        {"id": 3, "name": "Swimming Pool"}
    ]
}
```
<br>


```PUT /api/property/2/```

Request Body
```json
{
    "price": 50000,
    "location": {
        "city": "Newyork",
        "country": "USA"
    },
    "amenities": {
        "add": [
            {"name": "Fance"}
        ],
        "remove": [3],
        "update": {
            1: {"name": "Water"}
        }
    }
}
```
Note: Here add, remove and update are operators, so add operator create amenities with values specified in a list, remove operator dessociate amenities with id 3 from a property resource being updated, update operator edit amenity with id 1 according to values specified.

<br>

Response
```json
{
    "id": 2,
    "price": 50000,
    "location": {
        "id": 3,
        "city": "Newyork",
        "country": "USA"
    },
    "amenities": [
        {"id": 1, "name": "Water"},
        {"id": 2, "name": "Electricity"},
        {"id": 4, "name": "Fance"}
    ]
}
```