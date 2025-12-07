from django.urls import path

from plane.api.views import (
    ProjectEstimatePointAPIEndpoint,
    EstimateListCreateAPIEndpoint,
    EstimateDetailAPIEndpoint,
    EstimatePointListCreateAPIEndpoint,
    EstimatePointDetailAPIEndpoint,
)

urlpatterns = [
    # Project estimate points (active estimate)
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/project-estimates/",
        ProjectEstimatePointAPIEndpoint.as_view(http_method_names=["get"]),
        name="project-estimate-points",
    ),
    # Estimates CRUD
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/estimates/",
        EstimateListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="estimates",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/estimates/<uuid:pk>/",
        EstimateDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="estimates-detail",
    ),
    # Estimate points CRUD
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/estimates/<uuid:estimate_id>/estimate-points/",
        EstimatePointListCreateAPIEndpoint.as_view(http_method_names=["post"]),
        name="estimate-points",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/estimates/<uuid:estimate_id>/estimate-points/<uuid:pk>/",
        EstimatePointDetailAPIEndpoint.as_view(http_method_names=["patch", "delete"]),
        name="estimate-points-detail",
    ),
]
