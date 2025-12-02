"""
Solution (Knowledge Base) Views
"""

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cases.models import Solution
from cases.solution_serializers import (
    SolutionCreateUpdateSerializer,
    SolutionDetailSerializer,
    SolutionSerializer,
)


class SolutionListView(APIView, LimitOffsetPagination):
    """
    List and create solutions (Knowledge Base)
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="List all solutions with filters",
        parameters=[
            OpenApiParameter(
                "status", str, description="Filter by status (draft/reviewed/approved)"
            ),
            OpenApiParameter(
                "is_published", bool, description="Filter by published status"
            ),
            OpenApiParameter(
                "search", str, description="Search in title and description"
            ),
        ],
        responses={200: SolutionSerializer(many=True)},
    )
    def get(self, request):
        """List solutions with filters"""
        queryset = Solution.objects.filter(org=request.profile.org).order_by(
            "-created_at"
        )

        # Filters
        status_filter = request.query_params.get("status")
        is_published = request.query_params.get("is_published")
        search = request.query_params.get("search")

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == "true")

        if search:
            queryset = queryset.filter(title__icontains=search) | queryset.filter(
                description__icontains=search
            )

        # Paginate
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = SolutionSerializer(results, many=True)

        return self.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Create a new solution",
        request=SolutionCreateUpdateSerializer,
        responses={201: SolutionSerializer},
    )
    def post(self, request):
        """Create a new solution"""
        serializer = SolutionCreateUpdateSerializer(data=request.data)

        if serializer.is_valid():
            solution = serializer.save(org=request.profile.org, created_by=request.user)

            response_serializer = SolutionSerializer(solution)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SolutionDetailView(APIView):
    """
    Get, update, or delete a solution
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Get solution details",
        responses={200: SolutionDetailSerializer},
    )
    def get(self, request, pk):
        """Get solution details"""
        try:
            solution = Solution.objects.get(pk=pk, org=request.profile.org)
            serializer = SolutionDetailSerializer(solution)
            return Response(serializer.data)
        except Solution.DoesNotExist:
            return Response(
                {"error": "Solution not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Update solution",
        request=SolutionCreateUpdateSerializer,
        responses={200: SolutionSerializer},
    )
    def put(self, request, pk):
        """Update solution"""
        try:
            solution = Solution.objects.get(pk=pk, org=request.profile.org)

            serializer = SolutionCreateUpdateSerializer(solution, data=request.data)
            if serializer.is_valid():
                solution = serializer.save(updated_by=request.user)
                response_serializer = SolutionSerializer(solution)
                return Response(response_serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Solution.DoesNotExist:
            return Response(
                {"error": "Solution not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Partially update solution",
        request=SolutionCreateUpdateSerializer,
        responses={200: SolutionSerializer},
    )
    def patch(self, request, pk):
        """Partially update solution"""
        try:
            solution = Solution.objects.get(pk=pk, org=request.profile.org)

            serializer = SolutionCreateUpdateSerializer(
                solution, data=request.data, partial=True
            )
            if serializer.is_valid():
                solution = serializer.save(updated_by=request.user)
                response_serializer = SolutionSerializer(solution)
                return Response(response_serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Solution.DoesNotExist:
            return Response(
                {"error": "Solution not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Delete solution",
        responses={204: None},
    )
    def delete(self, request, pk):
        """Delete solution"""
        try:
            solution = Solution.objects.get(pk=pk, org=request.profile.org)
            solution.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Solution.DoesNotExist:
            return Response(
                {"error": "Solution not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SolutionPublishView(APIView):
    """
    Publish or unpublish a solution
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Publish an approved solution",
        request=None,
        responses={200: SolutionSerializer},
    )
    def post(self, request, pk):
        """Publish solution"""
        try:
            solution = Solution.objects.get(pk=pk, org=request.profile.org)

            if solution.status != "approved":
                return Response(
                    {
                        "error": "Only approved solutions can be published. Please approve it first."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            solution.publish()
            serializer = SolutionSerializer(solution)
            return Response(serializer.data)

        except Solution.DoesNotExist:
            return Response(
                {"error": "Solution not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SolutionUnpublishView(APIView):
    """
    Unpublish a solution
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Solutions (Knowledge Base)"],
        description="Unpublish a solution",
        request=None,
        responses={200: SolutionSerializer},
    )
    def post(self, request, pk):
        """Unpublish solution"""
        try:
            solution = Solution.objects.get(pk=pk, org=request.profile.org)
            solution.unpublish()
            serializer = SolutionSerializer(solution)
            return Response(serializer.data)

        except Solution.DoesNotExist:
            return Response(
                {"error": "Solution not found"}, status=status.HTTP_404_NOT_FOUND
            )
