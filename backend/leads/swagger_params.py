"""Schema-only parameter lists for drf-spectacular.

The ``org`` header parameter that used to lead every list here is gone; see
``common/swagger_params.py`` for why.
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

organization_params = []

lead_list_get_params = [
    OpenApiParameter("title", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("source", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter("assigned_to", OpenApiTypes.STR, OpenApiParameter.QUERY),
    OpenApiParameter(
        "status",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        enum=["assigned", "in process", "converted", "recycled", "closed"],
    ),
    OpenApiParameter("tags", OpenApiTypes.STR, OpenApiParameter.QUERY),
]
