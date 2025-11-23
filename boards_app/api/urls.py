from django.urls import path
from .views import BoardsView, BoardDetailView, EmailCheckView

urlpatterns = [
    path('', BoardsView.as_view(),  name='board-list-create'),
    path('<int:pk>/', BoardDetailView.as_view(),  name='board-event-create'),
    path('email-check/', EmailCheckView.as_view(),  name="board-email-check"),
]
