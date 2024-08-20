from django.urls import path
from store.views import CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView

urlpatterns = [
    path('all/', CategoryListView.as_view(), name='category-list'),
    path('add/', CategoryCreateView.as_view(), name='category-add'),
    path('<int:id>/update/', CategoryUpdateView.as_view(), name='category-update'),
    path('<int:id>/delete/', CategoryDeleteView.as_view(), name='category-delete'),
]
