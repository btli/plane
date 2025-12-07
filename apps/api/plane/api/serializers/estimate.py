# Third party imports
from rest_framework import serializers

# Module imports
from plane.db.models import Estimate, EstimatePoint
from .base import BaseSerializer


class EstimatePointSerializer(BaseSerializer):
    """
    Serializer for project estimation points and story point values.

    Handles numeric estimation data for work item sizing and sprint planning,
    providing standardized point values for project velocity calculations.
    """

    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Estimate points are required")
        value = data.get("value")
        if value and len(value) > 20:
            raise serializers.ValidationError("Value can't be more than 20 characters")
        return data

    class Meta:
        model = EstimatePoint
        fields = [
            "id",
            "key",
            "value",
            "description",
            "estimate",
            "workspace",
            "project",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "estimate",
            "workspace",
            "project",
            "created_at",
            "updated_at",
        ]


class EstimatePointLiteSerializer(BaseSerializer):
    """
    Lite serializer for estimate points (read-only).
    """

    class Meta:
        model = EstimatePoint
        fields = ["id", "key", "value"]
        read_only_fields = fields


class EstimateSerializer(BaseSerializer):
    """
    Serializer for project estimates.

    Handles estimate configuration including type and name.
    """

    class Meta:
        model = Estimate
        fields = [
            "id",
            "name",
            "description",
            "type",
            "last_used",
            "project",
            "workspace",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "workspace",
            "project",
            "created_at",
            "updated_at",
        ]


class EstimateReadSerializer(BaseSerializer):
    """
    Serializer for reading estimates with their points.
    """

    points = EstimatePointLiteSerializer(read_only=True, many=True)

    class Meta:
        model = Estimate
        fields = [
            "id",
            "name",
            "description",
            "type",
            "last_used",
            "points",
            "project",
            "workspace",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EstimateCreateSerializer(BaseSerializer):
    """
    Serializer for creating estimates with points.
    """

    estimate_points = EstimatePointSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Estimate
        fields = [
            "name",
            "description",
            "type",
            "last_used",
            "estimate_points",
        ]
