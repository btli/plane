"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AuthenticationWrapper } from "@/lib/wrappers/authentication-wrapper";
import { EPageTypes } from "@/helpers/authentication.helper";

type FlowState = "idle" | "ready" | "creating" | "sent" | "error" | "missing-port";

export default function CliConnectPage() {
  const searchParams = useSearchParams();
  const port = searchParams.get("port");
  const [token, setToken] = useState<string | null>(null);
  const [state, setState] = useState<FlowState>(port ? "ready" : "missing-port");
  const [error, setError] = useState<string | null>(null);

  const startIssuance = async () => {
    setState("creating");
    try {
      const response = await fetch("/api/cli/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ label: `plane-cli-${Date.now()}` }),
      });
      if (!response.ok) {
        throw new Error(`Failed to create token: ${response.status}`);
      }
      const result = (await response.json()) as { token: string };
      setToken(result.token);
      if (port) {
        // Send the token back to the CLI callback server
        await fetch(`http://localhost:${port}/plane-cli/callback?token=${result.token}&host=${window.location.host}`, {
          method: "GET",
          mode: "no-cors",
        }).catch(() => {
          // no-cors requests cannot be inspected; swallow errors to allow manual copy.
        });
      }
      setState("sent");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error while issuing token");
      setState("error");
    }
  };

  return (
    <AuthenticationWrapper pageType={EPageTypes.AUTHENTICATED}>
      <div className="flex min-h-screen items-center justify-center bg-custom-background-100 px-6">
        <div className="w-full max-w-xl space-y-4 rounded-md border border-custom-border-200 bg-custom-background-0 p-6 shadow">
          <h1 className="text-2xl font-semibold">Plane CLI authentication</h1>
          <p className="text-sm text-custom-text-400">
            This page issues a short-lived personal access token for the CLI and sends it back to the local
            callback server started by <code>plane auth</code>.
          </p>
          {state === "ready" && (
            <div className="space-y-2">
              <p className="text-sm text-custom-text-400">Ready to issue a token to your CLI.</p>
              <button
                type="button"
                className="rounded bg-custom-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-custom-primary-700"
                onClick={startIssuance}
              >
                Authorize CLI
              </button>
            </div>
          )}
          {state === "creating" && <p className="text-custom-text-200">Creating a token and contacting your CLI...</p>}
          {state === "sent" && (
            <div className="space-y-2">
              <p className="text-green-600">Token sent to your local CLI.</p>
              <p className="text-sm text-custom-text-400">
                If the terminal did not update automatically, copy the token below and run{" "}
                <code>plane auth --token &lt;token&gt;</code>.
              </p>
              {token && (
                <div className="rounded bg-custom-background-200 p-3 font-mono text-sm break-all">
                  {token}
                </div>
              )}
            </div>
          )}
          {state === "error" && (
            <div className="space-y-2">
              <p className="text-red-600">Unable to issue a token.</p>
              {error && <p className="text-sm text-custom-text-400">{error}</p>}
              <p className="text-sm text-custom-text-400">
                Ensure you are signed in, then reload this page or create a token from Account settings &gt; API tokens.
              </p>
            </div>
          )}
          {state === "missing-port" && (
            <div className="rounded border border-dashed border-custom-border-200 bg-custom-background-200 p-3 text-sm text-custom-text-400">
              No callback port was provided. Run <code>plane auth</code> from the CLI to open this page automatically.
            </div>
          )}
        </div>
      </div>
    </AuthenticationWrapper>
  );
}
