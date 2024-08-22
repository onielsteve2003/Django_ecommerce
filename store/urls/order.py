from django.urls import path
from ..views import OrderCreateView, OrderListView, OrderDetailView, OrderStatusUpdateView

urlpatterns = [
    path('create/', OrderCreateView.as_view(), name='order-create'),
    path('all/', OrderListView.as_view(), name='order-list'),
    path('<int:id>/', OrderDetailView.as_view(), name='order-detail'),
    path('<int:id>/status', OrderStatusUpdateView.as_view(), name='order-status-update'),
]
