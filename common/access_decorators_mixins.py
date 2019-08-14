from functools import wraps

from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def sales_access_required(function):
    """ this function is a decorator used to authorize if a user has sales access """
    def wrap(request, *args, **kwargs):
        if request.user.role == 'ADMIN' or request.user.is_superuser or request.user.has_sales_access:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


def marketing_access_required(function):
    """ this function is a decorator used to authorize if a user has marketing access """
    def wrap(request, *args, **kwargs):
        if request.user.role == 'ADMIN' or request.user.is_superuser or request.user.has_marketing_access:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap


class SalesAccessRequiredMixin(AccessMixin):
    """ Mixin used to authorize if a user has sales access  """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.raise_exception = True
        if request.user.role == 'ADMIN' or request.user.is_superuser or request.user.has_sales_access:
            return super(SalesAccessRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission()


class MarketingAccessRequiredMixin(AccessMixin):
    """ Mixin used to authorize if a user has marketing access  """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        self.raise_exception = True
        if request.user.role == 'ADMIN' or request.user.is_superuser or request.user.has_marketing_access:
            return super(MarketingAccessRequiredMixin, self).dispatch(request, *args, **kwargs)
        else:
            return self.handle_no_permission()


def admin_login_required(function):
    """ this function is a decorator used to authorize if a user is admin """
    def wrap(request, *args, **kwargs):
        if request.user.role == 'ADMIN' or request.user.is_superuser:
            return function(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return wrap