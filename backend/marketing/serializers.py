"""
Marketing App Serializers
"""

from rest_framework import serializers
from marketing.models import NewsletterSubscriber, ContactFormSubmission
from common.serializer import UserSerializer


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    """Serializer for newsletter subscribers"""

    class Meta:
        model = NewsletterSubscriber
        fields = [
            'id',
            'email',
            'is_active',
            'subscribed_at',
            'unsubscribed_at',
            'is_confirmed',
            'confirmed_at',
            'ip_address',
            'user_agent',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'subscribed_at',
            'unsubscribed_at',
            'confirmed_at',
            'created_at',
            'updated_at',
        ]


class NewsletterSubscribeSerializer(serializers.Serializer):
    """Serializer for public newsletter subscription"""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Check if email already subscribed"""
        if NewsletterSubscriber.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("This email is already subscribed to our newsletter.")
        return value

    def create(self, validated_data):
        """Create or reactivate subscription"""
        email = validated_data['email']

        # Check if previously unsubscribed
        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)
            if not subscriber.is_active:
                # Reactivate
                subscriber.is_active = True
                subscriber.unsubscribed_at = None
                subscriber.save()
                return subscriber
        except NewsletterSubscriber.DoesNotExist:
            pass

        # Create new subscriber
        subscriber = NewsletterSubscriber.objects.create(**validated_data)

        # Generate confirmation token
        import secrets
        subscriber.confirmation_token = secrets.token_urlsafe(32)
        subscriber.save()

        # TODO: Send confirmation email
        # send_newsletter_confirmation_email.delay(subscriber.id)

        return subscriber


class NewsletterUnsubscribeSerializer(serializers.Serializer):
    """Serializer for newsletter unsubscription"""
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=False, allow_blank=True)


class ContactFormSubmissionSerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions"""
    replied_by_details = UserSerializer(source='replied_by', read_only=True)

    class Meta:
        model = ContactFormSubmission
        fields = [
            'id',
            'name',
            'email',
            'message',
            'reason',
            'ip_address',
            'user_agent',
            'referrer',
            'status',
            'replied_by',
            'replied_by_details',
            'replied_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'replied_by',
            'replied_by_details',
            'replied_at',
            'created_at',
            'updated_at',
        ]


class ContactFormCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating contact form submissions (public)"""

    class Meta:
        model = ContactFormSubmission
        fields = [
            'name',
            'email',
            'message',
            'reason',
        ]

    def validate_email(self, value):
        """Basic email validation"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Please provide a valid email address.")
        return value

    def validate_message(self, value):
        """Ensure message is not too short"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value
