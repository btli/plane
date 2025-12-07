# Third party imports
from rest_framework import serializers

# Module imports
from .base import BaseSerializer
from plane.db.models import Page, PageVersion


class PageSerializer(BaseSerializer):
    """
    Serializer for project pages and documentation.

    Handles page metadata including ownership, access control, and organization.
    Provides fields for page hierarchy, favorites, and archive status.
    """

    is_favorite = serializers.BooleanField(read_only=True)
    label_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
    project_ids = serializers.ListField(child=serializers.UUIDField(), required=False)

    class Meta:
        model = Page
        fields = [
            "id",
            "name",
            "owned_by",
            "access",
            "color",
            "parent",
            "is_favorite",
            "is_locked",
            "archived_at",
            "workspace",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "view_props",
            "logo_props",
            "label_ids",
            "project_ids",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "owned_by",
            "is_favorite",
            "is_locked",
            "archived_at",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]


class PageDetailSerializer(PageSerializer):
    """
    Detailed serializer for project pages including content.

    Extends PageSerializer with HTML description content for full page retrieval.
    """

    description_html = serializers.CharField()

    class Meta(PageSerializer.Meta):
        fields = PageSerializer.Meta.fields + ["description_html"]


class PageCreateSerializer(BaseSerializer):
    """
    Serializer for creating new pages.
    """

    class Meta:
        model = Page
        fields = [
            "name",
            "access",
            "color",
            "parent",
            "view_props",
            "logo_props",
            "description_html",
        ]


class PageUpdateSerializer(BaseSerializer):
    """
    Serializer for updating existing pages.
    """

    class Meta:
        model = Page
        fields = [
            "name",
            "access",
            "color",
            "parent",
            "view_props",
            "logo_props",
            "description_html",
        ]


class PageVersionSerializer(BaseSerializer):
    """
    Serializer for page version history.
    """

    class Meta:
        model = PageVersion
        fields = [
            "id",
            "workspace",
            "page",
            "last_saved_at",
            "owned_by",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = fields


class PageVersionDetailSerializer(BaseSerializer):
    """
    Detailed serializer for page versions including content.
    """

    class Meta:
        model = PageVersion
        fields = [
            "id",
            "workspace",
            "page",
            "last_saved_at",
            "description_binary",
            "description_html",
            "description_json",
            "owned_by",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = fields
