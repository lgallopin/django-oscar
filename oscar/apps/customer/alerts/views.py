from django.views import generic
from django.db.models import get_model
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django import http

from oscar.core.loading import get_class
from oscar.apps.customer.alerts import utils

Product = get_model('catalogue', 'Product')
ProductAlert = get_model('customer', 'ProductAlert')
ProductAlertForm = get_class('customer.forms', 'ProductAlertForm')


class ProductAlertCreateView(generic.CreateView):
    """
    View to create a new product alert based on a registered user
    or an email address provided by an anonymous user.
    """
    model = ProductAlert
    form_class = ProductAlertForm
    template_name = 'customer/alerts/form.html'

    def get_context_data(self, **kwargs):
        ctx = super(ProductAlertCreateView, self).get_context_data(**kwargs)
        ctx['product'] = self.product
        ctx['alert_form'] = ctx.pop('form')
        return ctx

    def get(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
        return http.HttpResponseRedirect(product.get_absolute_url())

    def post(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=self.kwargs['pk'])
        return super(ProductAlertCreateView, self).post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(ProductAlertCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['product'] = self.product
        return kwargs

    def form_valid(self, form):
        response = super(ProductAlertCreateView, self).form_valid(form)
        if self.object.is_anonymous:
            utils.send_alert_confirmation(self.object)
        return response

    def get_success_url(self):
        if self.object.user:
            msg = _("An alert has been created")
        else:
            msg = _("An email has been sent to %s for confirmation") % self.object.email
        messages.success(self.request, msg)
        return self.object.product.get_absolute_url()


class ProductAlertRedirectView(generic.RedirectView):
    permanent = False

    def get(self, request, *args, **kwargs):
        self.alert = get_object_or_404(ProductAlert, key=kwargs['key'])
        self.update_alert()
        return super(ProductAlertRedirectView, self).get(request, *args, **kwargs)

    def get_redirect_url(self, **kwargs):
        return self.alert.product.get_absolute_url()


class ProductAlertConfirmView(ProductAlertRedirectView):
    permanent = False

    def update_alert(self):
        if self.alert.can_be_confirmed:
            self.alert.confirm()
            messages.success(self.request, _("Your stock alert is now active"))
        else:
            messages.error(self.request, _("Your stock alert cannot be confirmed"))


class ProductAlertCancelView(ProductAlertRedirectView):

    def update_alert(self):
        if self.alert.can_be_cancelled:
            self.alert.cancel()
            messages.success(self.request, _("Your stock alert has been cancelled"))
        else:
            messages.error(self.request, _("Your stock alert cannot be cancelled"))
