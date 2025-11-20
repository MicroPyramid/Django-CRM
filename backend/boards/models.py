from django.db import models
from common.base import BaseModel
from common.models import Org, Profile


class Board(BaseModel):
    """Kanban Board"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='owned_boards'
    )
    members = models.ManyToManyField(
        Profile,
        through='BoardMember',
        related_name='boards'
    )
    org = models.ForeignKey(
        Org,
        on_delete=models.CASCADE,
        related_name='boards'
    )
    is_archived = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'
        db_table = 'board'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class BoardMember(BaseModel):
    """Board membership with roles"""

    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    )

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='board_memberships'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')

    class Meta:
        verbose_name = 'Board Member'
        verbose_name_plural = 'Board Members'
        db_table = 'board_member'
        unique_together = ('board', 'profile')

    def __str__(self):
        return f"{self.profile} - {self.board} ({self.role})"


class BoardColumn(BaseModel):
    """Column in a board (e.g., To Do, In Progress, Done)"""

    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns'
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=7, default='#6B7280')  # Hex color
    limit = models.PositiveIntegerField(null=True, blank=True)  # WIP limit

    class Meta:
        verbose_name = 'Board Column'
        verbose_name_plural = 'Board Columns'
        db_table = 'board_column'
        ordering = ('order',)
        unique_together = ('board', 'name')

    def __str__(self):
        return f"{self.board.name} - {self.name}"


class BoardTask(BaseModel):
    """Task/Card in a board column"""

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    column = models.ForeignKey(
        BoardColumn,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    assigned_to = models.ManyToManyField(
        Profile,
        related_name='assigned_board_tasks',
        blank=True
    )
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Link to CRM entities (optional)
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='board_tasks'
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='board_tasks'
    )
    opportunity = models.ForeignKey(
        'opportunity.Opportunity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='board_tasks'
    )

    class Meta:
        verbose_name = 'Board Task'
        verbose_name_plural = 'Board Tasks'
        db_table = 'board_task'
        ordering = ('order',)

    def __str__(self):
        return self.title

    def mark_complete(self):
        """Mark task as completed"""
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.save()

    def mark_incomplete(self):
        """Mark task as incomplete"""
        self.completed_at = None
        self.save()

    @property
    def is_completed(self):
        return self.completed_at is not None

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and not self.is_completed:
            return timezone.now() > self.due_date
        return False
