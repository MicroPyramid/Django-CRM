"""
Marketing App Views
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import LimitOffsetPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from marketing.models import NewsletterSubscriber, ContactFormSubmission
from marketing.serializers import (
    NewsletterSubscriberSerializer,
    NewsletterSubscribeSerializer,
    NewsletterUnsubscribeSerializer,
    ContactFormSubmissionSerializer,
    ContactFormCreateSerializer,
)


# Newsletter Views

class NewsletterSubscriberListView(APIView, LimitOffsetPagination):
    """
    List and manage newsletter subscribers (Admin only)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Newsletter"],
        description="List all newsletter subscribers",
        parameters=[
            OpenApiParameter('is_active', bool, description='Filter by active status'),
            OpenApiParameter('is_confirmed', bool, description='Filter by confirmation status'),
            OpenApiParameter('email', str, description='Search by email'),
        ],
        responses={200: NewsletterSubscriberSerializer(many=True)}
    )
    def get(self, request):
        """List newsletter subscribers with filters"""
        queryset = NewsletterSubscriber.objects.all().order_by('-created_at')

        # Filters
        is_active = request.query_params.get('is_active')
        is_confirmed = request.query_params.get('is_confirmed')
        email_search = request.query_params.get('email')

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        if is_confirmed is not None:
            queryset = queryset.filter(is_confirmed=is_confirmed.lower() == 'true')

        if email_search:
            queryset = queryset.filter(email__icontains=email_search)

        # Paginate
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = NewsletterSubscriberSerializer(results, many=True)

        return self.get_paginated_response(serializer.data)


class NewsletterSubscribeView(APIView):
    """
    Public endpoint for newsletter subscription
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Newsletter"],
        description="Subscribe to newsletter (public endpoint)",
        request=NewsletterSubscribeSerializer,
        responses={201: NewsletterSubscriberSerializer}
    )
    def post(self, request):
        """Subscribe to newsletter"""
        serializer = NewsletterSubscribeSerializer(data=request.data)

        if serializer.is_valid():
            # Get IP and user agent from request
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            subscriber = serializer.save(
                ip_address=ip_address,
                user_agent=user_agent
            )

            response_serializer = NewsletterSubscriberSerializer(subscriber)
            return Response(
                {
                    'message': 'Successfully subscribed! Please check your email to confirm.',
                    'subscriber': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class NewsletterUnsubscribeView(APIView):
    """
    Public endpoint for newsletter unsubscription
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Newsletter"],
        description="Unsubscribe from newsletter (public endpoint)",
        request=NewsletterUnsubscribeSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    def post(self, request):
        """Unsubscribe from newsletter"""
        serializer = NewsletterUnsubscribeSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                subscriber = NewsletterSubscriber.objects.get(email=email, is_active=True)
                subscriber.unsubscribe()

                return Response(
                    {'message': 'Successfully unsubscribed from newsletter.'},
                    status=status.HTTP_200_OK
                )
            except NewsletterSubscriber.DoesNotExist:
                return Response(
                    {'message': 'Email not found in our subscription list.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewsletterConfirmView(APIView):
    """
    Confirm newsletter subscription via token
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Newsletter"],
        description="Confirm newsletter subscription",
        parameters=[OpenApiParameter('token', str, description='Confirmation token', required=True)],
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    def get(self, request):
        """Confirm subscription with token"""
        token = request.query_params.get('token')

        if not token:
            return Response(
                {'error': 'Confirmation token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subscriber = NewsletterSubscriber.objects.get(confirmation_token=token)
            subscriber.confirm_subscription()

            return Response(
                {'message': 'Email confirmed! You are now subscribed to our newsletter.'},
                status=status.HTTP_200_OK
            )
        except NewsletterSubscriber.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired confirmation token'},
                status=status.HTTP_404_NOT_FOUND
            )


# Contact Form Views

class ContactFormSubmissionListView(APIView, LimitOffsetPagination):
    """
    List contact form submissions (Admin only)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Contact Forms"],
        description="List all contact form submissions",
        parameters=[
            OpenApiParameter('status', str, description='Filter by status'),
            OpenApiParameter('reason', str, description='Filter by reason'),
            OpenApiParameter('email', str, description='Search by email'),
        ],
        responses={200: ContactFormSubmissionSerializer(many=True)}
    )
    def get(self, request):
        """List contact form submissions with filters"""
        queryset = ContactFormSubmission.objects.all().order_by('-created_at')

        # Filters
        status_filter = request.query_params.get('status')
        reason_filter = request.query_params.get('reason')
        email_search = request.query_params.get('email')

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if reason_filter:
            queryset = queryset.filter(reason=reason_filter)

        if email_search:
            queryset = queryset.filter(email__icontains=email_search)

        # Paginate
        results = self.paginate_queryset(queryset, request, view=self)
        serializer = ContactFormSubmissionSerializer(results, many=True)

        return self.get_paginated_response(serializer.data)


class ContactFormSubmissionDetailView(APIView):
    """
    Get, update, or delete a contact form submission
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Contact Forms"],
        description="Get contact form submission details",
        responses={200: ContactFormSubmissionSerializer}
    )
    def get(self, request, pk):
        """Get submission details"""
        try:
            submission = ContactFormSubmission.objects.get(pk=pk)
            submission.mark_as_read()  # Auto-mark as read
            serializer = ContactFormSubmissionSerializer(submission)
            return Response(serializer.data)
        except ContactFormSubmission.DoesNotExist:
            return Response(
                {'error': 'Submission not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        tags=["Contact Forms"],
        description="Update submission status",
        request=ContactFormSubmissionSerializer,
        responses={200: ContactFormSubmissionSerializer}
    )
    def patch(self, request, pk):
        """Update submission (e.g., mark as replied)"""
        try:
            submission = ContactFormSubmission.objects.get(pk=pk)

            # If marking as replied, record who replied
            if request.data.get('status') == 'replied' and submission.status != 'replied':
                submission.mark_as_replied(request.user)

            serializer = ContactFormSubmissionSerializer(submission, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ContactFormSubmission.DoesNotExist:
            return Response(
                {'error': 'Submission not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ContactFormSubmitView(APIView):
    """
    Public endpoint for contact form submission
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Contact Forms"],
        description="Submit contact form (public endpoint)",
        request=ContactFormCreateSerializer,
        responses={201: ContactFormSubmissionSerializer}
    )
    def post(self, request):
        """Submit contact form"""
        serializer = ContactFormCreateSerializer(data=request.data)

        if serializer.is_valid():
            # Get tracking data from request
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            referrer = request.META.get('HTTP_REFERER', '')

            submission = serializer.save(
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer
            )

            # TODO: Send notification email to admins
            # send_contact_form_notification.delay(submission.id)

            response_serializer = ContactFormSubmissionSerializer(submission)
            return Response(
                {
                    'message': 'Thank you for contacting us! We will respond shortly.',
                    'submission': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
