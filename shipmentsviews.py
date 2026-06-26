from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import IncomingShipment
from .forms import IncomingShipmentForm

class ShipmentRegisterView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = IncomingShipment
    form_class = IncomingShipmentForm
    template_name = 'shipments/shipment_register.html'
    success_url = reverse_lazy('shipments:list')
    permission_required = 'shipments.add_incomingshipment'

    def form_valid(self, form):
        form.instance.registered_by = self.request.user
        return super().form_valid(form)
