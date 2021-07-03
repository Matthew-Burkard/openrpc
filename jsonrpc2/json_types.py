from numbers import Number
from typing import Union, Optional

JSONPrimitive = Optional[Union[str, Number, bool]]
JSONArray = list[Union[JSONPrimitive, 'JSONObject', 'JSONArray']]
JSONObject = dict[str, Union[JSONPrimitive, 'JSONObject', 'JSONArray']]
JSON = Union[JSONPrimitive, JSONArray, JSONObject]
