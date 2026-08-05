"""Schema-only parameter lists for drf-spectacular.

The ``org`` header parameter that used to lead every list here is gone; see
``common/swagger_params.py`` for why.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params = []

account_get_params = [
    OpenApiParameter("name", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("city", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("tags", OpenApiTypes.STR, OpenApiParameter.QUERY),
]
