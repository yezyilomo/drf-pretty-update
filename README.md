# drf-pretty-update

Simple HTTP PUT request handler for Django REST Framework(DRF)

## Getting Started

```python
from drf_pretty_update import PrettyUpdate

class PropertySerializer(PrettyUpdate, serializers.ModelSerializer):
    pictures = PictureSerializer(many=True, read_only=True)
    location = LocationSerializer(many=False, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)
    class Meta:
        model = Property
        fields = (
            'id', 'price', 'location', 'amenities', 'pictures'
        )
```

```PUT /api/property/2/```

Request Body
```json
{
    "price": 40000,
    "location": 2,
    "amenities": [1,2,3]
}
```
Here all items on amenities(\*2many) will be replaced by those with ids `[1,2,3]`


To add or remove items on \*2many field use `add` and `remove` operator.
```PUT /api/property/2/```

Request Body
```json
{
    "price": 40000,
    "location": 2,
    "amenities": {
        "add": [4,5],
        "remove": [1, 3]
    }
}
```
