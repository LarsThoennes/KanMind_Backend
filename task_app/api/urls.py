from django.urls import path
from .views import TasksView, TaskCommentsView, TaskCommentDetailView, TaskDetailView, TasksAssignedToMeView, TasksReviewingView 

urlpatterns = [
    path('', TasksView.as_view(),  name='task-list-create'),
    path("<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),  
    path("<int:task_id>/comments/", TaskCommentsView.as_view(), name="task-comments"),
    path("<int:task_id>/comments/<int:comment_id>/", TaskCommentDetailView.as_view(), name="task-comment-detail"),
    path("assigned-to-me/", TasksAssignedToMeView.as_view(), name="tasks-assigned-to-me"),
    path("reviewing/", TasksReviewingView.as_view(), name="tasks-reviewing"),
]