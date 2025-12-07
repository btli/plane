from django.urls import path

from plane.app.views import CLICredentialTokenEndpoint

urlpatterns = [
    path("cli/token/", CLICredentialTokenEndpoint.as_view(), name="cli-token"),
]
