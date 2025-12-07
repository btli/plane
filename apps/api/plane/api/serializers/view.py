# Third party imports
from rest_framework import serializers

# Module imports
from .base import BaseSerializer
from plane.db.models import IssueView
from plane.utils.issue_filters import issue_filters


class IssueViewSerializer(BaseSerializer):
    """
    Serializer for issue views (saved filters).

    Handles view configuration including filters, display options, and access control.
    Supports both project-level and workspace-level views.
    """

    is_favorite = serializers.BooleanField(read_only=True)

    class Meta:
        model = IssueView
        fields = [
            "id",
            "name",
            "description",
            "filters",
            "display_filters",
            "display_properties",
            "query",
            "access",
            "is_locked",
            "is_favorite",
            "sort_order",
            "owned_by",
            "project",
            "workspace",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "project",
            "query",
            "owned_by",
            "is_favorite",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def create(self, validated_data):
        query_params = validated_data.get("filters", {})
        if bool(query_params):
            validated_data["query"] = issue_filters(query_params, "POST")
        else:
            validated_data["query"] = {}
        return IssueView.objects.create(**validated_data)

    def update(self, instance, validated_data):
        query_params = validated_data.get("filters", {})
        if bool(query_params):
            validated_data["query"] = issue_filters(query_params, "POST")
        else:
            validated_data["query"] = {}
        validated_data["query"] = issue_filters(query_params, "PATCH")
        return super().update(instance, validated_data)


class IssueViewCreateSerializer(BaseSerializer):
    """
    Serializer for creating new issue views.
    """

    class Meta:
        model = IssueView
        fields = [
            "name",
            "description",
            "filters",
            "display_filters",
            "display_properties",
            "access",
            "sort_order",
        ]


class IssueViewUpdateSerializer(BaseSerializer):
    """
    Serializer for updating existing issue views.
    """

    class Meta:
        model = IssueView
        fields = [
            "name",
            "description",
            "filters",
            "display_filters",
            "display_properties",
            "access",
            "sort_order",
            "is_locked",
        ]
