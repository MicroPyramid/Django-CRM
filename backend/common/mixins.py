# Python imports
import uuid

# Django imports
from common.models import models


class TimeAuditModel(models.Model):
    """To path when the record was created and last modified"""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Modified At")

    class Meta:
        abstract = True


class UserAuditModel(models.Model):
    """To path when the record was created and last modified"""

    created_by = models.ForeignKey(
        "common.User",
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
        verbose_name="Created By",
        null=True,
    )
    updated_by = models.ForeignKey(
        "common.User",
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated_by",
        verbose_name="Last Modified By",
        null=True,
    )

    class Meta:
        abstract = True


class AuditModel(TimeAuditModel, UserAuditModel):
    """To path when the record was created and last modified"""

    class Meta:
        abstract = True


from django.db.models import Q
from rest_framework.exceptions import NotFound, PermissionDenied


class OrgFilterMixin:
    """
    Mixin for API views that automatically filters querysets by organization.

    Usage:
        class LeadListView(OrgFilterMixin, APIView):
            model = Lead

            def get(self, request):
                queryset = self.get_org_queryset()
                # queryset is already filtered by org
    """

    model = None  # Override in subclass

    def get_org_queryset(self):
        """
        Get queryset filtered by the user's organization.

        Returns:
            QuerySet filtered by org, or empty queryset if no org context
        """
        if not hasattr(self, "model") or self.model is None:
            raise NotImplementedError("OrgFilterMixin requires 'model' attribute")

        if not hasattr(self.request, "profile") or self.request.profile is None:
            return self.model.objects.none()

        return self.model.objects.filter(org=self.request.profile.org)

    def get_org_object(self, pk):
        """
        Get a single object by pk, ensuring it belongs to user's org.

        Args:
            pk: Primary key of the object

        Returns:
            Model instance

        Raises:
            NotFound: If object doesn't exist or belongs to different org
        """
        try:
            obj = self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            raise NotFound(f"{self.model.__name__} not found")

        # Verify org ownership
        if hasattr(obj, "org_id"):
            if obj.org_id != self.request.profile.org_id:
                raise NotFound(f"{self.model.__name__} not found")

        return obj

    def filter_by_role(self, queryset):
        """
        Apply role-based filtering to queryset.

        Admins see all org data, users see only assigned/created items.

        Args:
            queryset: QuerySet already filtered by org

        Returns:
            QuerySet with role-based filtering applied
        """
        if self.request.profile.role == "ADMIN":
            return queryset

        # Non-admins see items they created or are assigned to
        filters = Q(created_by=self.request.profile.user)

        if hasattr(self.model, "assigned_to"):
            filters |= Q(assigned_to=self.request.profile)

        if hasattr(self.model, "teams"):
            user_team_ids = self.request.profile.user_teams.values_list("id", flat=True)
            filters |= Q(teams__id__in=user_team_ids)

        return queryset.filter(filters).distinct()


class OrgCreateMixin:
    """
    Mixin for API views that automatically sets org on object creation.

    Usage:
        class LeadCreateView(OrgCreateMixin, APIView):
            model = Lead
            serializer_class = LeadSerializer

            def post(self, request):
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid():
                    instance = self.perform_org_create(serializer)
                    return Response(...)
    """

    def perform_org_create(self, serializer):
        """
        Save serializer with org and created_by set automatically.

        Args:
            serializer: Valid serializer instance

        Returns:
            Created model instance
        """
        return serializer.save(
            org=self.request.profile.org, created_by=self.request.profile.user
        )

    def get_org_context(self):
        """
        Get org-related context for serializer.

        Returns:
            Dict with org and profile for serializer context
        """
        return {
            "org": self.request.profile.org,
            "profile": self.request.profile,
            "user": self.request.profile.user,
        }


class OrgUpdateMixin:
    """
    Mixin for API views that validates org ownership on update.

    Usage:
        class LeadUpdateView(OrgUpdateMixin, OrgFilterMixin, APIView):
            model = Lead

            def put(self, request, pk):
                instance = self.get_org_object(pk)
                self.validate_update_permission(instance)
                # proceed with update
    """

    def validate_update_permission(self, instance):
        """
        Validate user has permission to update this instance.

        Args:
            instance: Model instance to update

        Raises:
            PermissionDenied: If user cannot update this instance
        """
        # Verify org ownership
        if hasattr(instance, "org_id"):
            if instance.org_id != self.request.profile.org_id:
                raise PermissionDenied("Cannot update object from another organization")

        # Admins can update anything in their org
        if self.request.profile.role == "ADMIN":
            return

        # Check if user created the object
        if hasattr(instance, "created_by_id"):
            if instance.created_by_id == self.request.profile.user_id:
                return

        # Check if user is assigned
        if hasattr(instance, "assigned_to"):
            if self.request.profile in instance.assigned_to.all():
                return

        raise PermissionDenied("You don't have permission to update this object")


class OrgDeleteMixin:
    """
    Mixin for API views that validates org ownership on delete.

    Usage:
        class LeadDeleteView(OrgDeleteMixin, OrgFilterMixin, APIView):
            model = Lead

            def delete(self, request, pk):
                instance = self.get_org_object(pk)
                self.validate_delete_permission(instance)
                instance.delete()
    """

    def validate_delete_permission(self, instance):
        """
        Validate user has permission to delete this instance.

        Args:
            instance: Model instance to delete

        Raises:
            PermissionDenied: If user cannot delete this instance
        """
        # Verify org ownership
        if hasattr(instance, "org_id"):
            if instance.org_id != self.request.profile.org_id:
                raise PermissionDenied("Cannot delete object from another organization")

        # Only admins and creators can delete
        if self.request.profile.role == "ADMIN":
            return

        if hasattr(instance, "created_by_id"):
            if instance.created_by_id == self.request.profile.user_id:
                return

        raise PermissionDenied("You don't have permission to delete this object")


class OrgViewMixin(OrgFilterMixin, OrgCreateMixin, OrgUpdateMixin, OrgDeleteMixin):
    """
    Combined mixin for standard CRUD operations with org isolation.

    Usage:
        class LeadView(OrgViewMixin, APIView):
            model = Lead
            serializer_class = LeadSerializer

            def get(self, request, pk=None):
                if pk:
                    instance = self.get_org_object(pk)
                    return Response(self.serializer_class(instance).data)
                queryset = self.filter_by_role(self.get_org_queryset())
                return Response(self.serializer_class(queryset, many=True).data)

            def post(self, request):
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid():
                    instance = self.perform_org_create(serializer)
                    return Response(self.serializer_class(instance).data)

            def put(self, request, pk):
                instance = self.get_org_object(pk)
                self.validate_update_permission(instance)
                serializer = self.serializer_class(instance, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)

            def delete(self, request, pk):
                instance = self.get_org_object(pk)
                self.validate_delete_permission(instance)
                instance.delete()
                return Response(status=204)
    """

    pass


class ActivityTrackingMixin:
    """
    Mixin to automatically track activities on CRUD operations.

    Usage:
        class LeadView(ActivityTrackingMixin, OrgViewMixin, APIView):
            model = Lead
            entity_type = 'Lead'
    """

    entity_type = None  # Override in subclass

    def track_activity(self, action, instance, description=""):
        """
        Create an activity record for the action.

        Args:
            action: Action type (CREATE, UPDATE, DELETE, VIEW)
            instance: Model instance
            description: Optional description
        """
        from common.models import Activity

        if not self.entity_type:
            return

        entity_name = ""
        if hasattr(instance, "name"):
            entity_name = instance.name
        elif hasattr(instance, "title"):
            entity_name = instance.title
        elif hasattr(instance, "first_name"):
            entity_name = f"{instance.first_name} {getattr(instance, 'last_name', '')}"

        Activity.objects.create(
            user=self.request.profile,
            action=action,
            entity_type=self.entity_type,
            entity_id=instance.id,
            entity_name=entity_name[:255],
            description=description[:500] if description else "",
            org=self.request.profile.org,
        )


class BulkOperationMixin:
    """
    Mixin for bulk operations with org validation.

    Usage:
        class LeadBulkView(BulkOperationMixin, OrgFilterMixin, APIView):
            model = Lead

            def post(self, request):
                ids = request.data.get('ids', [])
                instances = self.get_bulk_objects(ids)
                # perform bulk operation
    """

    def get_bulk_objects(self, ids):
        """
        Get multiple objects by ids, ensuring all belong to user's org.

        Args:
            ids: List of primary keys

        Returns:
            QuerySet of objects

        Raises:
            PermissionDenied: If any object belongs to different org
        """
        queryset = self.model.objects.filter(pk__in=ids)

        # Verify all objects belong to user's org
        for obj in queryset:
            if hasattr(obj, "org_id"):
                if obj.org_id != self.request.profile.org_id:
                    raise PermissionDenied(
                        "One or more objects do not belong to your organization"
                    )

        return queryset

    def bulk_update(self, ids, update_data):
        """
        Bulk update objects with org validation.

        Args:
            ids: List of primary keys
            update_data: Dict of fields to update

        Returns:
            Number of updated objects
        """
        queryset = self.get_bulk_objects(ids)
        return queryset.update(**update_data)

    def bulk_delete(self, ids):
        """
        Bulk delete objects with org validation.

        Args:
            ids: List of primary keys

        Returns:
            Number of deleted objects
        """
        queryset = self.get_bulk_objects(ids)
        count = queryset.count()
        queryset.delete()
        return count
