from datetime import datetime, timezone

import json
import logging
import re
from typing import Any

_LOGGER = logging.getLogger(__name__)


def json_loads(s: str) -> Any:
    return json.loads(s, object_hook=obj_parser)


def obj_parser(obj) -> Any:
    """Parse datetime."""
    for key, val in obj.items():
        try:
            if isinstance(val, str):
                if val in ("false", "False", "FALSE"):
                    obj[key] = False
                elif val in ("true", "True", "TRUE"):
                    obj[key] = True
                else:
                    obj[key] = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            # dtVal  = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S%z")
            # if dtVal.tzinfo is None:
            #    dtVal  = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
            # obj[key] = dtVal
        except (TypeError, ValueError):
            pass
    return obj


def camel2slug(s: str) -> str:
    """Convert camelCase to camel_case.

    >>> camel2slug('fooBar')
    'foo_bar'
    """
    return re.sub("([A-Z])", "_\\1", s).lower().lstrip("_")
