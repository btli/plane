from django.urls import path

from plane.api.views import (
    ProjectViewListCreateAPIEndpoint,
    ProjectViewDetailAPIEndpoint,
    ProjectViewFavoriteAPIEndpoint,
    WorkspaceViewListCreateAPIEndpoint,
    WorkspaceViewDetailAPIEndpoint,
)

urlpatterns = [
    # Project views
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/views/",
        ProjectViewListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="project-views",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/views/<uuid:pk>/",
        ProjectViewDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="project-views-detail",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/views/<uuid:pk>/favorite/",
        ProjectViewFavoriteAPIEndpoint.as_view(http_method_names=["post", "delete"]),
        name="project-views-favorite",
    ),
    # Workspace views
    path(
        "workspaces/<str:slug>/views/",
        WorkspaceViewListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="workspace-views",
    ),
    path(
        "workspaces/<str:slug>/views/<uuid:pk>/",
        WorkspaceViewDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="workspace-views-detail",
    ),
]
