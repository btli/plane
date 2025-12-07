from django.urls import path

from plane.api.views import (
    StateListCreateAPIEndpoint,
    StateDetailAPIEndpoint,
    StateMarkDefaultAPIEndpoint,
)

urlpatterns = [
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/states/",
        StateListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="states",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/states/<uuid:state_id>/",
        StateDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="states",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/states/<uuid:pk>/mark-default/",
        StateMarkDefaultAPIEndpoint.as_view(http_method_names=["post"]),
        name="states-mark-default",
    ),
]
