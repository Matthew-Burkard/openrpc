from numbers import Number
from typing import Union, Optional

JSONPrimitive = Optional[Union[str, Number, bool]]
JSONArray = list['JSON']
JSONObject = dict[str, 'JSON']
JSONStructured = Union[JSONObject, JSONArray]
JSON = Union[JSONPrimitive, JSONStructured]
