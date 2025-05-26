from django.urls import path
from . import views

app_name = 'log'

urlpatterns = [
    # Corresponds to LogController GET /logs (list) and POST /logs (create)
    path('', views.log_list_and_create_view, name='log_list_create'),

    # Corresponds to LogController PATCH /logs/{id} (update)
    # GET to display form, POST to submit (view then makes PATCH to backend)
    path('<int:log_id>/update/', views.log_update_form_view, name='log_update_form'),

    # Corresponds to LogController DELETE /logs/{id} (delete)
    # GET to display confirmation, POST to submit (view then makes DELETE to backend)
    path('<int:log_id>/delete/', views.log_delete_confirmation_view, name='log_delete_confirm'),

    # Corresponds to LogController POST /logs/{id}/verify?action={action} (verify)
    # POST to trigger verification
    path('<int:log_id>/verify/', views.log_verify_action_view, name='log_verify_action'),

    # Corresponds to LogController GET /logs/{id}/messages (list messages)
    # and POST /logs/{id}/messages (add message)
    path('<int:log_id>/messages/', views.message_list_and_add_view, name='message_list_add'),

    path('applications/status/', views.view_application_status, name='view_application_status'),
]
