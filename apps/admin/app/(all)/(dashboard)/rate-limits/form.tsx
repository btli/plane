import { observer } from "mobx-react";
import { useForm } from "react-hook-form";
import { Gauge, Shield, Mail, Image, Users, Globe, AlertTriangle } from "lucide-react";
// plane imports
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IFormattedInstanceConfiguration } from "@plane/types";
// components
import { ControllerInput } from "@/components/common/controller-input";
// hooks
import { useInstance } from "@/hooks/store";

interface IRateLimitsForm {
  RATE_LIMIT_API_KEY: string;
  RATE_LIMIT_SERVICE_TOKEN: string;
  RATE_LIMIT_AUTHENTICATION: string;
  RATE_LIMIT_EMAIL_VERIFICATION: string;
  RATE_LIMIT_ASSET: string;
  RATE_LIMIT_ANONYMOUS: string;
}

interface Props {
  config: IFormattedInstanceConfiguration;
}

const RATE_LIMIT_FIELDS = [
  {
    key: "RATE_LIMIT_API_KEY" as const,
    label: "API Key Rate Limit",
    description: "Rate limit for authenticated API requests using API keys",
    icon: Gauge,
    placeholder: "60/minute",
    helpText: "Format: number/period (e.g., 60/minute, 1000/hour, 10000/day)",
  },
  {
    key: "RATE_LIMIT_SERVICE_TOKEN" as const,
    label: "Service Token Rate Limit",
    description: "Rate limit for service-to-service API requests",
    icon: Shield,
    placeholder: "300/minute",
    helpText: "Higher limit for automated service integrations",
  },
  {
    key: "RATE_LIMIT_AUTHENTICATION" as const,
    label: "Authentication Rate Limit",
    description: "Rate limit for login, signup, and password reset endpoints",
    icon: Users,
    placeholder: "30/minute",
    helpText: "Protects against brute-force attacks",
  },
  {
    key: "RATE_LIMIT_EMAIL_VERIFICATION" as const,
    label: "Email Verification Rate Limit",
    description: "Rate limit for email verification code generation",
    icon: Mail,
    placeholder: "3/hour",
    helpText: "Prevents email spam abuse",
  },
  {
    key: "RATE_LIMIT_ASSET" as const,
    label: "Asset Upload Rate Limit",
    description: "Rate limit for file uploads per asset",
    icon: Image,
    placeholder: "5/minute",
    helpText: "Per-asset rate limiting",
  },
  {
    key: "RATE_LIMIT_ANONYMOUS" as const,
    label: "Anonymous Rate Limit",
    description: "Rate limit for unauthenticated API requests",
    icon: Globe,
    placeholder: "30/minute",
    helpText: "Protects public endpoints",
  },
];

export const RateLimitsConfigurationForm = observer(function RateLimitsConfigurationForm({ config }: Props) {
  const { updateInstanceConfigurations } = useInstance();

  const {
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<IRateLimitsForm>({
    defaultValues: {
      RATE_LIMIT_API_KEY: config["RATE_LIMIT_API_KEY"] || "60/minute",
      RATE_LIMIT_SERVICE_TOKEN: config["RATE_LIMIT_SERVICE_TOKEN"] || "300/minute",
      RATE_LIMIT_AUTHENTICATION: config["RATE_LIMIT_AUTHENTICATION"] || "30/minute",
      RATE_LIMIT_EMAIL_VERIFICATION: config["RATE_LIMIT_EMAIL_VERIFICATION"] || "3/hour",
      RATE_LIMIT_ASSET: config["RATE_LIMIT_ASSET"] || "5/minute",
      RATE_LIMIT_ANONYMOUS: config["RATE_LIMIT_ANONYMOUS"] || "30/minute",
    },
  });

  const onSubmit = async (formData: IRateLimitsForm) => {
    // Validate rate limit format
    const rateRegex = /^\d+\/(second|minute|hour|day)$/;
    for (const [key, value] of Object.entries(formData)) {
      if (!rateRegex.test(value)) {
        setToast({
          type: TOAST_TYPE.ERROR,
          title: "Invalid format",
          message: `${key.replace("RATE_LIMIT_", "")} must be in format: number/period (e.g., 60/minute)`,
        });
        return;
      }
    }

    await updateInstanceConfigurations(formData)
      .then(() =>
        setToast({
          type: TOAST_TYPE.SUCCESS,
          title: "Success",
          message: "Rate limits updated successfully. Changes will take effect shortly.",
        })
      )
      .catch((err) => {
        console.error(err);
        setToast({
          type: TOAST_TYPE.ERROR,
          title: "Error",
          message: "Failed to update rate limits",
        });
      });
  };

  return (
    <div className="space-y-8">
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-md p-4 flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-sm text-amber-600">
          <strong>Note:</strong> Rate limit changes may take up to 2 hours to take effect due to caching. Setting very
          high limits may impact instance performance and security.
        </div>
      </div>

      <div className="space-y-6">
        {RATE_LIMIT_FIELDS.map((field) => (
          <div key={field.key} className="border border-custom-border-200 rounded-lg p-4">
            <div className="flex items-start gap-4">
              <div className="shrink-0">
                <div className="flex items-center justify-center w-10 h-10 bg-custom-background-80 rounded-full">
                  <field.icon className="w-5 h-5 text-custom-text-300" />
                </div>
              </div>
              <div className="flex-grow space-y-3">
                <div>
                  <div className="text-sm font-medium text-custom-text-100">{field.label}</div>
                  <div className="text-xs text-custom-text-300">{field.description}</div>
                </div>
                <div className="max-w-xs">
                  <ControllerInput
                    name={field.key}
                    control={control}
                    type="text"
                    placeholder={field.placeholder}
                    error={Boolean(errors[field.key])}
                  />
                  <div className="text-xs text-custom-text-400 mt-1">{field.helpText}</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div>
        <Button variant="primary" onClick={handleSubmit(onSubmit)} loading={isSubmitting}>
          {isSubmitting ? "Saving..." : "Save changes"}
        </Button>
      </div>
    </div>
  );
});
