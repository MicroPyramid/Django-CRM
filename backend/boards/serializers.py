from rest_framework import serializers
from boards.models import Board, BoardColumn, BoardTask, BoardMember
from common.serializer import ProfileSerializer


class BoardMemberSerializer(serializers.ModelSerializer):
    """Serializer for board members"""

    profile = ProfileSerializer(read_only=True)
    profile_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = BoardMember
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'board')


class BoardTaskSerializer(serializers.ModelSerializer):
    """Serializer for board tasks"""

    assigned_to = ProfileSerializer(many=True, read_only=True)
    assigned_to_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    is_completed = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = BoardTask
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'completed_at')


class BoardColumnSerializer(serializers.ModelSerializer):
    """Serializer for board columns"""

    tasks = BoardTaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = BoardColumn
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'board')

    def get_task_count(self, obj):
        return obj.tasks.count()


class BoardColumnListSerializer(serializers.ModelSerializer):
    """Simplified column serializer for lists"""

    task_count = serializers.SerializerMethodField()

    class Meta:
        model = BoardColumn
        fields = ['id', 'name', 'order', 'color', 'limit', 'task_count']

    def get_task_count(self, obj):
        return obj.tasks.count()


class BoardSerializer(serializers.ModelSerializer):
    """Serializer for boards"""

    owner = ProfileSerializer(read_only=True)
    columns = BoardColumnListSerializer(many=True, read_only=True)
    members = BoardMemberSerializer(source='memberships', many=True, read_only=True)
    member_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'owner', 'org')

    def get_member_count(self, obj):
        return obj.members.count()

    def get_task_count(self, obj):
        return BoardTask.objects.filter(column__board=obj).count()


class BoardListSerializer(serializers.ModelSerializer):
    """Simplified board serializer for lists"""

    owner = ProfileSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    column_count = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'name', 'description', 'owner', 'is_archived',
                  'member_count', 'column_count', 'task_count', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count()

    def get_column_count(self, obj):
        return obj.columns.count()

    def get_task_count(self, obj):
        return BoardTask.objects.filter(column__board=obj).count()
