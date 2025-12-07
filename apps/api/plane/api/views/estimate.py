# Python imports
import json
import random
import string

# Django imports
from django.utils import timezone

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.api.serializers import (
    EstimatePointSerializer,
    EstimatePointLiteSerializer,
    EstimateReadSerializer,
)
from plane.app.permissions import ProjectEntityPermission
from plane.db.models import Project, Estimate, EstimatePoint, Issue
from plane.utils.cache import invalidate_cache
from plane.bgtasks.issue_activities_task import issue_activity
from .base import BaseAPIView


def generate_random_name(length=10):
    """Generate a random name for estimates without a name."""
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


class ProjectEstimatePointAPIEndpoint(BaseAPIView):
    """
    Project Estimate Point Endpoint

    Returns the estimate points for the current project's estimate.
    """

    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get(self, request, slug, project_id):
        """Get project estimate points"""
        project = Project.objects.get(workspace__slug=slug, pk=project_id)

        if project.estimate_id is not None:
            estimate_points = EstimatePoint.objects.filter(
                estimate_id=project.estimate_id,
                project_id=project_id,
                workspace__slug=slug,
            )
            serializer = EstimatePointLiteSerializer(estimate_points, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response([], status=status.HTTP_200_OK)


class EstimateListCreateAPIEndpoint(BaseAPIView):
    """
    Estimate List and Create Endpoint

    Supports listing all estimates and creating new estimates with points.
    """

    serializer_class = EstimateReadSerializer
    model = Estimate
    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get(self, request, slug, project_id):
        """List all estimates for a project"""
        estimates = (
            Estimate.objects.filter(workspace__slug=slug, project_id=project_id)
            .prefetch_related("points")
            .select_related("workspace", "project")
        )
        serializer = EstimateReadSerializer(estimates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @invalidate_cache(path="/api/workspaces/:slug/estimates/", url_params=True, user=False)
    def post(self, request, slug, project_id):
        """Create a new estimate with points"""
        estimate_data = request.data.get("estimate", {})
        estimate_name = estimate_data.get("name", generate_random_name())
        estimate_type = estimate_data.get("type", "categories")
        last_used = estimate_data.get("last_used", False)

        project = Project.objects.get(workspace__slug=slug, pk=project_id)

        estimate = Estimate.objects.create(
            name=estimate_name,
            project_id=project_id,
            workspace_id=project.workspace_id,
            last_used=last_used,
            type=estimate_type,
        )

        estimate_points = request.data.get("estimate_points", [])

        if estimate_points:
            serializer = EstimatePointSerializer(data=estimate_points, many=True)
            if not serializer.is_valid():
                estimate.delete()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            EstimatePoint.objects.bulk_create(
                [
                    EstimatePoint(
                        estimate=estimate,
                        key=point.get("key", 0),
                        value=point.get("value", ""),
                        description=point.get("description", ""),
                        project_id=project_id,
                        workspace_id=estimate.workspace_id,
                    )
                    for point in estimate_points
                ],
                batch_size=10,
                ignore_conflicts=True,
            )

        serializer = EstimateReadSerializer(estimate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EstimateDetailAPIEndpoint(BaseAPIView):
    """
    Estimate Detail, Update, and Delete Endpoint
    """

    serializer_class = EstimateReadSerializer
    model = Estimate
    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get(self, request, slug, project_id, pk):
        """Retrieve a specific estimate"""
        estimate = Estimate.objects.get(pk=pk, workspace__slug=slug, project_id=project_id)
        serializer = EstimateReadSerializer(estimate)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @invalidate_cache(path="/api/workspaces/:slug/estimates/", url_params=True, user=False)
    def patch(self, request, slug, project_id, pk):
        """Update an estimate and its points"""
        estimate_points_data = request.data.get("estimate_points", [])

        if not estimate_points_data:
            return Response(
                {"error": "Estimate points are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estimate = Estimate.objects.get(pk=pk, workspace__slug=slug, project_id=project_id)

        # Update estimate metadata if provided
        if request.data.get("estimate"):
            estimate.name = request.data.get("estimate").get("name", estimate.name)
            estimate.type = request.data.get("estimate").get("type", estimate.type)
            estimate.save()

        # Update estimate points
        estimate_points = EstimatePoint.objects.filter(
            pk__in=[point.get("id") for point in estimate_points_data if point.get("id")],
            workspace__slug=slug,
            project_id=project_id,
            estimate_id=pk,
        )

        updated_estimate_points = []
        for estimate_point in estimate_points:
            point_data = [p for p in estimate_points_data if p.get("id") == str(estimate_point.id)]
            if point_data:
                estimate_point.value = point_data[0].get("value", estimate_point.value)
                estimate_point.key = point_data[0].get("key", estimate_point.key)
                updated_estimate_points.append(estimate_point)

        EstimatePoint.objects.bulk_update(updated_estimate_points, ["key", "value"], batch_size=10)

        serializer = EstimateReadSerializer(estimate)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @invalidate_cache(path="/api/workspaces/:slug/estimates/", url_params=True, user=False)
    def delete(self, request, slug, project_id, pk):
        """Delete an estimate"""
        estimate = Estimate.objects.get(pk=pk, workspace__slug=slug, project_id=project_id)
        estimate.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EstimatePointListCreateAPIEndpoint(BaseAPIView):
    """
    Estimate Point List and Create Endpoint
    """

    permission_classes = [ProjectEntityPermission]

    def post(self, request, slug, project_id, estimate_id):
        """Create a new estimate point"""
        if not request.data.get("key") or not request.data.get("value"):
            return Response(
                {"error": "Key and value are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estimate = Estimate.objects.get(pk=estimate_id, workspace__slug=slug, project_id=project_id)

        estimate_point = EstimatePoint.objects.create(
            estimate_id=estimate_id,
            project_id=project_id,
            workspace_id=estimate.workspace_id,
            key=request.data.get("key", 0),
            value=request.data.get("value", ""),
            description=request.data.get("description", ""),
        )

        serializer = EstimatePointSerializer(estimate_point)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EstimatePointDetailAPIEndpoint(BaseAPIView):
    """
    Estimate Point Detail, Update, and Delete Endpoint
    """

    permission_classes = [ProjectEntityPermission]

    def patch(self, request, slug, project_id, estimate_id, pk):
        """Update an estimate point"""
        estimate_point = EstimatePoint.objects.get(
            pk=pk,
            estimate_id=estimate_id,
            project_id=project_id,
            workspace__slug=slug,
        )

        serializer = EstimatePointSerializer(estimate_point, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, slug, project_id, estimate_id, pk):
        """Delete an estimate point"""
        new_estimate_id = request.data.get("new_estimate_id", None)

        estimate_points = EstimatePoint.objects.filter(
            estimate_id=estimate_id, project_id=project_id, workspace__slug=slug
        )

        # Update all issues with the new estimate if provided
        if new_estimate_id:
            issues = Issue.objects.filter(
                project_id=project_id,
                workspace__slug=slug,
                estimate_point_id=pk,
            )
            for issue in issues:
                issue_activity.delay(
                    type="issue.activity.updated",
                    requested_data=json.dumps({"estimate_point": (str(new_estimate_id) if new_estimate_id else None)}),
                    actor_id=str(request.user.id),
                    issue_id=issue.id,
                    project_id=str(project_id),
                    current_instance=json.dumps(
                        {"estimate_point": (str(issue.estimate_point_id) if issue.estimate_point_id else None)}
                    ),
                    epoch=int(timezone.now().timestamp()),
                )
            issues.update(estimate_point_id=new_estimate_id)
        else:
            issues = Issue.objects.filter(
                project_id=project_id,
                workspace__slug=slug,
                estimate_point_id=pk,
            )
            for issue in issues:
                issue_activity.delay(
                    type="issue.activity.updated",
                    requested_data=json.dumps({"estimate_point": None}),
                    actor_id=str(request.user.id),
                    issue_id=issue.id,
                    project_id=str(project_id),
                    current_instance=json.dumps(
                        {"estimate_point": (str(issue.estimate_point_id) if issue.estimate_point_id else None)}
                    ),
                    epoch=int(timezone.now().timestamp()),
                )
            issues.update(estimate_point_id=None)

        # Delete the estimate point
        old_estimate_point = EstimatePoint.objects.filter(pk=pk).first()

        if old_estimate_point:
            # Rearrange the estimate points
            updated_estimate_points = []
            for estimate_point in estimate_points:
                if estimate_point.key > old_estimate_point.key:
                    estimate_point.key -= 1
                    updated_estimate_points.append(estimate_point)

            EstimatePoint.objects.bulk_update(updated_estimate_points, ["key"], batch_size=10)
            old_estimate_point.delete()

        return Response(
            EstimatePointSerializer(updated_estimate_points, many=True).data,
            status=status.HTTP_200_OK,
        )
