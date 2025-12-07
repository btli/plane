# Python imports
from datetime import datetime

# Django imports
from django.db import connection
from django.db.models import (
    Exists,
    OuterRef,
    Q,
    Value,
    UUIDField,
)
from django.contrib.postgres.aggregates import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.db.models.functions import Coalesce

# Third party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from plane.api.serializers import (
    PageSerializer,
    PageDetailSerializer,
    PageCreateSerializer,
    PageUpdateSerializer,
    PageVersionSerializer,
    PageVersionDetailSerializer,
)
from plane.app.permissions import ProjectEntityPermission
from plane.db.models import (
    Page,
    PageLabel,
    PageLog,
    UserFavorite,
    ProjectMember,
    ProjectPage,
    Project,
    PageVersion,
)
from .base import BaseAPIView
from plane.bgtasks.page_transaction_task import page_transaction


def unarchive_archive_page_and_descendants(page_id, archived_at):
    """Archive or unarchive a page and all its descendants."""
    sql = """
    WITH RECURSIVE descendants AS (
        SELECT id FROM pages WHERE id = %s
        UNION ALL
        SELECT pages.id FROM pages, descendants WHERE pages.parent_id = descendants.id
    )
    UPDATE pages SET archived_at = %s WHERE id IN (SELECT id FROM descendants);
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [page_id, archived_at])


class PageListCreateAPIEndpoint(BaseAPIView):
    """Page List and Create Endpoint"""

    serializer_class = PageSerializer
    model = Page
    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get_queryset(self):
        subquery = UserFavorite.objects.filter(
            user=self.request.user,
            entity_type="page",
            entity_identifier=OuterRef("pk"),
            workspace__slug=self.kwargs.get("slug"),
        )
        return (
            Page.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(
                projects__project_projectmember__member=self.request.user,
                projects__project_projectmember__is_active=True,
                projects__archived_at__isnull=True,
            )
            .filter(parent__isnull=True)
            .filter(Q(owned_by=self.request.user) | Q(access=0))
            .prefetch_related("projects")
            .select_related("workspace")
            .select_related("owned_by")
            .annotate(is_favorite=Exists(subquery))
            .order_by(self.request.GET.get("order_by", "-created_at"))
            .prefetch_related("labels")
            .order_by("-is_favorite", "-created_at")
            .annotate(
                project=Exists(
                    ProjectPage.objects.filter(
                        page_id=OuterRef("id"),
                        project_id=self.kwargs.get("project_id"),
                    )
                )
            )
            .annotate(
                label_ids=Coalesce(
                    ArrayAgg(
                        "page_labels__label_id",
                        distinct=True,
                        filter=~Q(page_labels__label_id__isnull=True),
                    ),
                    Value([], output_field=ArrayField(UUIDField())),
                ),
                project_ids=Coalesce(
                    ArrayAgg("projects__id", distinct=True, filter=~Q(projects__id=True)),
                    Value([], output_field=ArrayField(UUIDField())),
                ),
            )
            .filter(project=True)
            .distinct()
        )

    def get(self, request, slug, project_id):
        """List pages"""
        queryset = self.get_queryset().filter(archived_at__isnull=True)
        project = Project.objects.get(pk=project_id)

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
            on_results=lambda pages: PageSerializer(pages, many=True, fields=self.fields, expand=self.expand).data,
        )

    def post(self, request, slug, project_id):
        """Create page"""
        project = Project.objects.get(workspace__slug=slug, pk=project_id)

        serializer = PageCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Create the page
            page = Page.objects.create(
                name=serializer.validated_data.get("name", "Untitled"),
                description_html=serializer.validated_data.get("description_html", "<p></p>"),
                access=serializer.validated_data.get("access", 0),
                color=serializer.validated_data.get("color", ""),
                parent=serializer.validated_data.get("parent"),
                view_props=serializer.validated_data.get("view_props", {}),
                logo_props=serializer.validated_data.get("logo_props", {}),
                owned_by=request.user,
                workspace_id=project.workspace_id,
            )

            # Create the project page
            ProjectPage.objects.create(
                workspace_id=page.workspace_id,
                project_id=project_id,
                page_id=page.id,
            )

            # Handle labels if provided
            labels = request.data.get("labels", [])
            if labels:
                PageLabel.objects.bulk_create(
                    [
                        PageLabel(
                            label_id=label_id,
                            page=page,
                            workspace_id=page.workspace_id,
                        )
                        for label_id in labels
                    ],
                    batch_size=10,
                )

            # Capture the page transaction
            page_transaction.delay(
                new_description_html=serializer.validated_data.get("description_html", "<p></p>"),
                old_description_html=None,
                page_id=page.id,
            )

            page = self.get_queryset().get(pk=page.id)
            return Response(
                PageDetailSerializer(page).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PageDetailAPIEndpoint(BaseAPIView):
    """Page Detail, Update, and Delete Endpoint"""

    serializer_class = PageDetailSerializer
    model = Page
    permission_classes = [ProjectEntityPermission]
    use_read_replica = True

    def get_queryset(self):
        subquery = UserFavorite.objects.filter(
            user=self.request.user,
            entity_type="page",
            entity_identifier=OuterRef("pk"),
            workspace__slug=self.kwargs.get("slug"),
        )
        return (
            Page.objects.filter(workspace__slug=self.kwargs.get("slug"))
            .filter(
                projects__project_projectmember__member=self.request.user,
                projects__project_projectmember__is_active=True,
                projects__archived_at__isnull=True,
            )
            .filter(Q(owned_by=self.request.user) | Q(access=0))
            .prefetch_related("projects")
            .select_related("workspace")
            .select_related("owned_by")
            .annotate(is_favorite=Exists(subquery))
            .annotate(
                project=Exists(
                    ProjectPage.objects.filter(
                        page_id=OuterRef("id"),
                        project_id=self.kwargs.get("project_id"),
                    )
                )
            )
            .annotate(
                label_ids=Coalesce(
                    ArrayAgg(
                        "page_labels__label_id",
                        distinct=True,
                        filter=~Q(page_labels__label_id__isnull=True),
                    ),
                    Value([], output_field=ArrayField(UUIDField())),
                ),
                project_ids=Coalesce(
                    ArrayAgg("projects__id", distinct=True, filter=~Q(projects__id=True)),
                    Value([], output_field=ArrayField(UUIDField())),
                ),
            )
            .filter(project=True)
            .distinct()
        )

    def get(self, request, slug, project_id, pk):
        """Retrieve page"""
        page = self.get_queryset().filter(pk=pk).first()
        project = Project.objects.get(pk=project_id)

        if page is None:
            return Response({"error": "Page not found"}, status=status.HTTP_404_NOT_FOUND)

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
            and not page.owned_by == request.user
        ):
            return Response(
                {"error": "You are not allowed to view this page"},
                status=status.HTTP_403_FORBIDDEN,
            )

        issue_ids = PageLog.objects.filter(page_id=pk, entity_name="issue").values_list("entity_identifier", flat=True)

        data = PageDetailSerializer(page).data
        data["issue_ids"] = list(issue_ids)

        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request, slug, project_id, pk):
        """Update page"""
        page = Page.objects.get(
            pk=pk,
            workspace__slug=slug,
            projects__id=project_id,
            project_pages__deleted_at__isnull=True,
        )

        if page.is_locked:
            return Response(
                {"error": "Page is locked"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only update access if the page owner is the requesting user
        if page.access != request.data.get("access", page.access) and page.owned_by_id != request.user.id:
            return Response(
                {"error": "Access cannot be updated since this page is owned by someone else"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Handle parent validation
        parent = request.data.get("parent", None)
        if parent:
            Page.objects.get(
                pk=parent,
                workspace__slug=slug,
                projects__id=project_id,
                project_pages__deleted_at__isnull=True,
            )

        serializer = PageUpdateSerializer(page, data=request.data, partial=True)
        page_description = page.description_html

        if serializer.is_valid():
            serializer.save()

            # Capture the page transaction
            if request.data.get("description_html"):
                page_transaction.delay(
                    new_description_html=request.data.get("description_html", "<p></p>"),
                    old_description_html=page_description,
                    page_id=pk,
                )

            page = self.get_queryset().get(pk=pk)
            return Response(PageDetailSerializer(page).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug, project_id, pk):
        """Delete page"""
        page = Page.objects.get(
            pk=pk,
            workspace__slug=slug,
            projects__id=project_id,
            project_pages__deleted_at__isnull=True,
        )

        if page.archived_at is None:
            return Response(
                {"error": "The page should be archived before deleting"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check permissions
        if page.owned_by_id != request.user.id and (
            not ProjectMember.objects.filter(
                workspace__slug=slug,
                member=request.user,
                role=20,
                project_id=project_id,
                is_active=True,
            ).exists()
        ):
            return Response(
                {"error": "Only admin or owner can delete the page"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Remove parent from all children
        Page.objects.filter(
            parent_id=pk,
            projects__id=project_id,
            workspace__slug=slug,
            project_pages__deleted_at__isnull=True,
        ).update(parent=None)

        page.delete()

        # Delete user favorites
        UserFavorite.objects.filter(
            project=project_id,
            workspace__slug=slug,
            entity_identifier=pk,
            entity_type="page",
        ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class PageArchiveUnarchiveAPIEndpoint(BaseAPIView):
    """Page Archive and Unarchive Endpoint"""

    permission_classes = [ProjectEntityPermission]

    def post(self, request, slug, project_id, pk):
        """Archive page"""
        page = Page.objects.get(
            pk=pk,
            workspace__slug=slug,
            projects__id=project_id,
            project_pages__deleted_at__isnull=True,
        )

        # Only the owner or admin can archive the page
        if (
            ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                is_active=True,
                role__lte=15,
            ).exists()
            and request.user.id != page.owned_by_id
        ):
            return Response(
                {"error": "Only the owner or admin can archive the page"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        UserFavorite.objects.filter(
            entity_type="page",
            entity_identifier=pk,
            project_id=project_id,
            workspace__slug=slug,
        ).delete()

        unarchive_archive_page_and_descendants(pk, datetime.now())

        return Response({"archived_at": str(datetime.now())}, status=status.HTTP_200_OK)

    def delete(self, request, slug, project_id, pk):
        """Unarchive page"""
        page = Page.objects.get(
            pk=pk,
            workspace__slug=slug,
            projects__id=project_id,
            project_pages__deleted_at__isnull=True,
        )

        # Only the owner or admin can unarchive the page
        if (
            ProjectMember.objects.filter(
                project_id=project_id,
                member=request.user,
                is_active=True,
                role__lte=15,
            ).exists()
            and request.user.id != page.owned_by_id
        ):
            return Response(
                {"error": "Only the owner or admin can unarchive the page"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If parent is archived, break hierarchy
        if page.parent_id and page.parent.archived_at:
            page.parent = None
            page.save(update_fields=["parent"])

        unarchive_archive_page_and_descendants(pk, None)

        return Response(status=status.HTTP_204_NO_CONTENT)


class PageLockUnlockAPIEndpoint(BaseAPIView):
    """Page Lock and Unlock Endpoint"""

    permission_classes = [ProjectEntityPermission]

    def post(self, request, slug, project_id, pk):
        """Lock page"""
        page = Page.objects.get(
            pk=pk,
            workspace__slug=slug,
            projects__id=project_id,
            project_pages__deleted_at__isnull=True,
        )
        page.is_locked = True
        page.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, slug, project_id, pk):
        """Unlock page"""
        page = Page.objects.get(
            pk=pk,
            workspace__slug=slug,
            projects__id=project_id,
            project_pages__deleted_at__isnull=True,
        )
        page.is_locked = False
        page.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageFavoriteAPIEndpoint(BaseAPIView):
    """Page Favorite Endpoint"""

    permission_classes = [ProjectEntityPermission]

    def post(self, request, slug, project_id, pk):
        """Add page to favorites"""
        UserFavorite.objects.create(
            project_id=project_id,
            entity_identifier=pk,
            entity_type="page",
            user=request.user,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, slug, project_id, pk):
        """Remove page from favorites"""
        page_favorite = UserFavorite.objects.get(
            project=project_id,
            user=request.user,
            workspace__slug=slug,
            entity_identifier=pk,
            entity_type="page",
        )
        page_favorite.delete(soft=False)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageVersionAPIEndpoint(BaseAPIView):
    """Page Version Endpoint"""

    permission_classes = [ProjectEntityPermission]

    def get(self, request, slug, project_id, page_id, pk=None):
        """List or retrieve page versions"""
        if pk:
            # Retrieve specific version
            version = PageVersion.objects.get(
                pk=pk,
                page_id=page_id,
                workspace__slug=slug,
            )
            return Response(PageVersionDetailSerializer(version).data, status=status.HTTP_200_OK)
        else:
            # List versions
            versions = PageVersion.objects.filter(
                page_id=page_id,
                workspace__slug=slug,
            ).order_by("-created_at")

            return self.paginate(
                request=request,
                queryset=versions,
                on_results=lambda versions: PageVersionSerializer(versions, many=True).data,
            )
