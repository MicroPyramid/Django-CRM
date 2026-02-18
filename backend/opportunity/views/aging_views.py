from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import HasOrgContext
from common.utils import STAGES
from opportunity.models import StageAgingConfig
from opportunity.serializer import StageAgingConfigSerializer
from opportunity.workflow import CLOSED_STAGES, DEFAULT_STAGE_EXPECTED_DAYS


class StageAgingConfigView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)

    def get(self, request):
        """Return aging config for all open stages, with defaults for unconfigured stages."""
        org = request.profile.org
        configs = {
            c.stage: c
            for c in StageAgingConfig.objects.filter(org=org)
        }

        result = []
        for stage_value, stage_label in STAGES:
            if stage_value in CLOSED_STAGES:
                continue
            if stage_value in configs:
                serializer = StageAgingConfigSerializer(configs[stage_value])
                result.append(serializer.data)
            else:
                result.append({
                    "id": None,
                    "stage": stage_value,
                    "expected_days": DEFAULT_STAGE_EXPECTED_DAYS.get(stage_value, 14),
                    "warning_days": None,
                })
        return Response(result)

    def put(self, request):
        """Bulk upsert stage aging configs (admin only)."""
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": True, "errors": "Only admins can update aging config"},
                status=status.HTTP_403_FORBIDDEN,
            )

        org = request.profile.org
        configs_data = request.data
        if not isinstance(configs_data, list):
            return Response(
                {"error": True, "errors": "Expected a list of stage configs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        for item in configs_data:
            stage = item.get("stage")
            if not stage or stage in CLOSED_STAGES:
                continue

            config, _ = StageAgingConfig.objects.update_or_create(
                org=org,
                stage=stage,
                defaults={
                    "expected_days": item.get("expected_days", 14),
                    "warning_days": item.get("warning_days"),
                },
            )
            results.append(StageAgingConfigSerializer(config).data)

        return Response(
            {"error": False, "message": "Aging config updated", "configs": results},
            status=status.HTTP_200_OK,
        )
