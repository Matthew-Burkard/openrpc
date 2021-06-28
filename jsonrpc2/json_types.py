from numbers import Number
from typing import Union, Optional, List, Dict

JSONPrimitive = Optional[Union[str, Number, bool]]
JSONArray = List[Union[JSONPrimitive, 'JSONObject', 'JSONArray']]
JSONObject = Dict[str, Union[JSONPrimitive, 'JSONObject', 'JSONArray']]
JSON = Union[JSONPrimitive, JSONArray, JSONObject]
