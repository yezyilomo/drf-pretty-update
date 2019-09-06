# drf-pretty-update
This is a collection of simple and flexible model serializer and fields for Django REST Framework which allows you to create/update your models with related nested data.


## Installing

`pip install drf-pretty-update`


## Getting Started
drf-pretty-update has two components, `NestedModelSerializer` and `NestedField`. A serializer `NestedModelSerializer` has `update` and `create` logics for nested fields on the other hand `NestedField` is used to validate data before dispatching update or create.


### Using NestedField
```python
from app.models import Location, Amenity, Property
from drf_pretty_update.serializers import NestedModelSerializer
from drf_pretty_update.fields import NestedField


class LocationSerializer(NestedModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "city", "country")


class AmenitySerializer(NestedModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name")
        

class PropertySerializer(NestedModelSerializer):
    location = NestedField(LocationSerializer)
    amenities = NestedField(AmenitySerializer, many=True)
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
    "amenities": {
        "add": [3],
        "create": [
            {"name": "Watererr"},
            {"name": "Electricity"}
        ]
    }
}
```
What's done here is pretty clear, location will be created and associated with the property created, also create operation on amenities will create amenities with values specified in a list and associate with the property, add operation will add amenity with id 4 to a list of amenities of the property.

**Note**: POST for many related field supports two operations which are `create` and `add`.

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
        "add": [4],
        "create": [{"name": "Fance"}],
        "remove": [3],
        "update": {1: {"name": "Water"}}
    }
}
```
**Note**: Here `add`, `create`, `remove` and `update` are operations, so `add` operation add amenitiy with id 4 to a list of amenities of the property, `create` operation create amenities with values specified in a list, `remove` operation dessociate amenities with id 3 from a property, `update` operation edit amenity with id 1 according to values specified.

**Note**: PUT/PATCH for many related field supports four operations which are `create`, `add`, `remove` and `update`.

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
        {"id": 4, "name": "Bathtub"},
        {"id": 5, "name": "Fance"}
    ]
}
```
<br>
<br>


### Using NestedField with `accept_pk=True` kwarg.
`accept_pk=True` is used if you want to update nested field by using pk/id of existing data(basically associate and dessociate existing nested resources with the parent resource without actually mutating the nested resource). This applies to ForeignKey relation only.

```python
from app.models import Location, Amenity, Property
from drf_pretty_update.serializers import NestedModelSerializer 
from drf_pretty_update.fields import NestedField


class LocationSerializer(NestedModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "city", "country")


class PropertySerializer(NestedModelSerializer):
    location = NestedField(ocationSerializer, accept_pk=True)
    class Meta:
        model = Property
        fields = (
            'id', 'price', 'location'
        )
```
<br>


```POST /api/property/```

Request Body
```json
{
    "price": 40000,
    "location": 2
}
```
**Note**: Here location resource with id 2 is already existing, so what's done here is create new property resource and associate it with a location with id 2.
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
    }
}
```
<br>


### Using NestedField with `create_ops=[..]` and `update_ops=[..]` kwargs.
You can restrict some operations by using `create_ops` and `update_ops` keyword arguments as follows

```python
from app.models import Location, Amenity, Property
from drf_pretty_update.serializers import NestedModelSerializer 
from drf_pretty_update.fields import NestedField


class AmenitySerializer(NestedModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name")
        

class PropertySerializer(NestedModelSerializer):
    amenities = NestedField(
        AmenitySerializer, 
        many=True,
        create_ops=["add"],  # Allow only add operation(restrict create operation)
        update_ops=["add", "remove"]  # Allow only add and remove operations(restrict create and update operations)
    )
    class Meta:
        model = Property
        fields = (
            'id', 'price', 'amenities'
        )
```
<br>


```POST /api/property/```

Request Body
```json
{
    "price": 60000,
    "amenities": {
        "add": [1, 2]
    }
}
```
**Note**: According to `create_ops=["add"]`, you can't use `create` operation in here!.
<br>

Response
```json
{
    "id": 2,
    "price": 60000,
    "amenities": [
        {"id": 1, "name": "Watererr"},
        {"id": 2, "name": "Electricity"}
    ]
}
```
<br>


```PUT /api/property/2/```

Request Body
```json
{
    "price": 50000,
    "amenities": {
        "add": [3],
        "remove": [2]
    }
}
```
**Note**: According to `update_ops=["add", "remove"]`, you can't use `create` or `update` operation in here!.
<br>

Response
```json
{
    "id": 2,
    "price": 50000,
    "amenities": [
        {"id": 1, "name": "Water"},
        {"id": 3, "name": "Bathtub"}
    ]
}
```
<br>


## Running Tests

`python setup.py test`