# Django imports
from django.db.models import Exists, OuterRef, Q
from django.db import transaction

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.api.serializers import (
    IssueViewSerializer,
    IssueViewCreateSerializer,
    IssueViewUpdateSerializer,
)
from plane.app.permissions import ProjectEntityPermission, WorkspaceEntityPermission
from plane.db.models import (
    IssueView,
    Workspace,
    WorkspaceMember,
    ProjectMember,
    Project,
    UserFavorite,
)
from .base import BaseAPIView


class ProjectViewListCreateAPIEndpoint(BaseAPIView):
    """Project View List and Create Endpoint"""

    serializer_class = IssueViewSerializer
    model = IssueView
    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get_queryset(self):
        subquery = UserFavorite.objects.filter(
            user=self.request.user,
            entity_identifier=OuterRef("pk"),
            entity_type="view",
            project_id=self.kwargs.get("project_id"),
            workspace__slug=self.kwargs.get("slug"),
        )
        return (
            IssueView.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(
                project__project_projectmember__member=self.request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .filter(Q(owned_by=self.request.user) | Q(access=1))
            .select_related("project")
            .select_related("workspace")
            .annotate(is_favorite=Exists(subquery))
            .order_by("-is_favorite", "name")
            .distinct()
        )

    def get(self, request, slug, project_id):
        """List project views"""
        queryset = self.get_queryset()
        project = Project.objects.get(id=project_id)

        # Filter for guest users
        if (
            ProjectMember.objects.filter(
                workspace__slug=slug,
                project_id=project_id,
                member=request.user,
                role=5,
                is_active=True,
            ).exists()
            and not project.guest_view_all_features
        ):
            queryset = queryset.filter(owned_by=request.user)

        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda views: IssueViewSerializer(views, many=True, fields=self.fields, expand=self.expand).data,
        )

    def post(self, request, slug, project_id):
        """Create project view"""
        workspace = Workspace.objects.get(slug=slug)

        serializer = IssueViewCreateSerializer(data=request.data)
        if serializer.is_valid():
            view = serializer.save(
                project_id=project_id,
                workspace_id=workspace.id,
                owned_by=request.user,
            )
            return Response(
                IssueViewSerializer(view).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectViewDetailAPIEndpoint(BaseAPIView):
    """Project View Detail, Update, and Delete Endpoint"""

    serializer_class = IssueViewSerializer
    model = IssueView
    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get_queryset(self):
        subquery = UserFavorite.objects.filter(
            user=self.request.user,
            entity_identifier=OuterRef("pk"),
            entity_type="view",
            project_id=self.kwargs.get("project_id"),
            workspace__slug=self.kwargs.get("slug"),
        )
        return (
            IssueView.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(
                project__project_projectmember__member=self.request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .filter(Q(owned_by=self.request.user) | Q(access=1))
            .select_related("project")
            .select_related("workspace")
            .annotate(is_favorite=Exists(subquery))
            .distinct()
        )

    def get(self, request, slug, project_id, pk):
        """Retrieve project view"""
        view = self.get_queryset().filter(pk=pk).first()
        project = Project.objects.get(id=project_id)

        if view is None:
            return Response({"error": "View not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check guest permissions
        if (
            ProjectMember.objects.filter(
                workspace__slug=slug,
                project_id=project_id,
                member=request.user,
                role=5,
                is_active=True,
            ).exists()
            and not project.guest_view_all_features
            and view.owned_by != request.user
        ):
            return Response(
                {"error": "You are not allowed to view this view"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(IssueViewSerializer(view).data, status=status.HTTP_200_OK)

    def patch(self, request, slug, project_id, pk):
        """Update project view"""
        with transaction.atomic():
            view = IssueView.objects.select_for_update().get(pk=pk, workspace__slug=slug, project_id=project_id)

            if view.is_locked:
                return Response(
                    {"error": "View is locked"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Only update the view if owner is updating
            if view.owned_by_id != request.user.id:
                return Response(
                    {"error": "Only the owner of the view can update the view"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = IssueViewUpdateSerializer(view, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                view = self.get_queryset().get(pk=pk)
                return Response(IssueViewSerializer(view).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug, project_id, pk):
        """Delete project view"""
        view = IssueView.objects.get(pk=pk, project_id=project_id, workspace__slug=slug)

        # Check permissions
        if (
            ProjectMember.objects.filter(
                workspace__slug=slug,
                project_id=project_id,
                member=request.user,
                role=20,
                is_active=True,
            ).exists()
            or view.owned_by_id == request.user.id
        ):
            view.delete()
            # Delete user favorites
            UserFavorite.objects.filter(
                project_id=project_id,
                workspace__slug=slug,
                entity_identifier=pk,
                entity_type="view",
            ).delete()
        else:
            return Response(
                {"error": "Only admin or owner can delete the view"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectViewFavoriteAPIEndpoint(BaseAPIView):
    """Project View Favorite Endpoint"""

    permission_classes = [ProjectEntityPermission]

    def post(self, request, slug, project_id, pk):
        """Add view to favorites"""
        UserFavorite.objects.create(
            user=request.user,
            entity_identifier=pk,
            entity_type="view",
            project_id=project_id,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, slug, project_id, pk):
        """Remove view from favorites"""
        view_favorite = UserFavorite.objects.get(
            project=project_id,
            user=request.user,
            workspace__slug=slug,
            entity_type="view",
            entity_identifier=pk,
        )
        view_favorite.delete(soft=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceViewListCreateAPIEndpoint(BaseAPIView):
    """Workspace View List and Create Endpoint"""

    serializer_class = IssueViewSerializer
    model = IssueView
    permission_classes = [WorkspaceEntityPermission]
    use_read_replica = True

    def get_queryset(self):
        return (
            IssueView.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project__isnull=True)
            .filter(Q(owned_by=self.request.user) | Q(access=1))
            .order_by(self.request.GET.get("order_by", "-created_at"))
            .distinct()
        )

    def get(self, request, slug):
        """List workspace views"""
        queryset = self.get_queryset()

        # Filter for guest users
        if WorkspaceMember.objects.filter(workspace__slug=slug, member=request.user, role=5, is_active=True).exists():
            queryset = queryset.filter(owned_by=request.user)

        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda views: IssueViewSerializer(views, many=True, fields=self.fields, expand=self.expand).data,
        )

    def post(self, request, slug):
        """Create workspace view"""
        workspace = Workspace.objects.get(slug=slug)

        serializer = IssueViewCreateSerializer(data=request.data)
        if serializer.is_valid():
            view = serializer.save(
                workspace_id=workspace.id,
                owned_by=request.user,
            )
            return Response(
                IssueViewSerializer(view).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceViewDetailAPIEndpoint(BaseAPIView):
    """Workspace View Detail, Update, and Delete Endpoint"""

    serializer_class = IssueViewSerializer
    model = IssueView
    permission_classes = [WorkspaceEntityPermission]
    use_read_replica = True

    def get_queryset(self):
        return (
            IssueView.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project__isnull=True)
            .filter(Q(owned_by=self.request.user) | Q(access=1))
            .distinct()
        )

    def get(self, request, slug, pk):
        """Retrieve workspace view"""
        view = self.get_queryset().filter(pk=pk).first()

        if view is None:
            return Response({"error": "View not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(IssueViewSerializer(view).data, status=status.HTTP_200_OK)

    def patch(self, request, slug, pk):
        """Update workspace view"""
        with transaction.atomic():
            view = IssueView.objects.select_for_update().get(pk=pk, workspace__slug=slug)

            if view.is_locked:
                return Response(
                    {"error": "View is locked"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Only update the view if owner is updating
            if view.owned_by_id != request.user.id:
                return Response(
                    {"error": "Only the owner of the view can update the view"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = IssueViewUpdateSerializer(view, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response(IssueViewSerializer(view).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug, pk):
        """Delete workspace view"""
        view = IssueView.objects.get(pk=pk, workspace__slug=slug)

        # Check permissions
        workspace_admin = WorkspaceMember.objects.filter(
            workspace__slug=slug, member=request.user, role=20, is_active=True
        ).exists()

        if workspace_admin or view.owned_by == request.user:
            view.delete()
            # Delete user favorites
            UserFavorite.objects.filter(
                workspace__slug=slug,
                entity_identifier=pk,
                project__isnull=True,
                entity_type="view",
            ).delete()
        else:
            return Response(
                {"error": "Only admin or owner can delete the view"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
