# Implementation Plan: Configurable Rate Limits in Admin Panel

## Overview

Add the ability for instance administrators to configure API rate limits through the God Mode admin panel. This allows self-hosted Plane instances to adjust rate limiting based on their specific needs.

## Current Rate Limit Architecture

The existing rate limiting system uses Django REST Framework throttling with these components:

| Component | Location | Current Rate | Purpose |
|-----------|----------|--------------|---------|
| `ApiKeyRateThrottle` | `apps/api/plane/api/rate_limit.py` | `60/minute` (env: `API_KEY_RATE_LIMIT`) | Standard API key requests |
| `ServiceTokenRateThrottle` | `apps/api/plane/api/rate_limit.py` | `300/minute` | Service-to-service API calls |
| `AuthenticationThrottle` | `apps/api/plane/authentication/rate_limit.py` | `30/minute` | Login/auth endpoints |
| `EmailVerificationThrottle` | `apps/api/plane/authentication/rate_limit.py` | `3/hour` | Email verification codes |
| `AssetRateThrottle` | `apps/api/plane/throttles/asset.py` | `5/minute` (from settings) | Asset uploads per asset ID |
| Default anon throttle | `apps/api/plane/settings/common.py` | `30/minute` | Anonymous requests |

## Proposed Configuration Keys

Add the following instance configuration variables:

```python
# Category: RATE_LIMITS
RATE_LIMIT_API_KEY = "60/minute"          # API key requests
RATE_LIMIT_SERVICE_TOKEN = "300/minute"   # Service token requests
RATE_LIMIT_AUTHENTICATION = "30/minute"   # Auth endpoints
RATE_LIMIT_EMAIL_VERIFICATION = "3/hour"  # Email verification
RATE_LIMIT_ASSET = "5/minute"             # Asset operations
RATE_LIMIT_ANONYMOUS = "30/minute"        # Anonymous requests
```

## Implementation Steps

### Phase 1: Backend Configuration (Priority: High)

#### 1.1 Add Rate Limit Configuration Variables

**File:** `apps/api/plane/utils/instance_config_variables/core.py`

```python
rate_limit_config_variables = [
    {
        "key": "RATE_LIMIT_API_KEY",
        "value": os.environ.get("RATE_LIMIT_API_KEY", "60/minute"),
        "category": "RATE_LIMITS",
        "is_encrypted": False,
    },
    {
        "key": "RATE_LIMIT_SERVICE_TOKEN",
        "value": os.environ.get("RATE_LIMIT_SERVICE_TOKEN", "300/minute"),
        "category": "RATE_LIMITS",
        "is_encrypted": False,
    },
    {
        "key": "RATE_LIMIT_AUTHENTICATION",
        "value": os.environ.get("RATE_LIMIT_AUTHENTICATION", "30/minute"),
        "category": "RATE_LIMITS",
        "is_encrypted": False,
    },
    {
        "key": "RATE_LIMIT_EMAIL_VERIFICATION",
        "value": os.environ.get("RATE_LIMIT_EMAIL_VERIFICATION", "3/hour"),
        "category": "RATE_LIMITS",
        "is_encrypted": False,
    },
    {
        "key": "RATE_LIMIT_ASSET",
        "value": os.environ.get("RATE_LIMIT_ASSET", "5/minute"),
        "category": "RATE_LIMITS",
        "is_encrypted": False,
    },
    {
        "key": "RATE_LIMIT_ANONYMOUS",
        "value": os.environ.get("RATE_LIMIT_ANONYMOUS", "30/minute"),
        "category": "RATE_LIMITS",
        "is_encrypted": False,
    },
]

# Add to core_config_variables list
core_config_variables = [
    ...
    *rate_limit_config_variables,
]
```

#### 1.2 Update Throttle Classes to Read from Configuration

**File:** `apps/api/plane/api/rate_limit.py`

```python
from plane.license.utils.instance_value import get_configuration_value

class ApiKeyRateThrottle(SimpleRateThrottle):
    scope = "api_key"

    @property
    def rate(self):
        (rate_limit,) = get_configuration_value([
            {"key": "RATE_LIMIT_API_KEY", "default": os.environ.get("API_KEY_RATE_LIMIT", "60/minute")}
        ])
        return rate_limit or "60/minute"

    # ... rest remains the same
```

**File:** `apps/api/plane/authentication/rate_limit.py`

```python
from plane.license.utils.instance_value import get_configuration_value

class AuthenticationThrottle(AnonRateThrottle):
    scope = "authentication"

    @property
    def rate(self):
        (rate_limit,) = get_configuration_value([
            {"key": "RATE_LIMIT_AUTHENTICATION", "default": "30/minute"}
        ])
        return rate_limit or "30/minute"

class EmailVerificationThrottle(UserRateThrottle):
    scope = "email_verification"

    @property
    def rate(self):
        (rate_limit,) = get_configuration_value([
            {"key": "RATE_LIMIT_EMAIL_VERIFICATION", "default": "3/hour"}
        ])
        return rate_limit or "3/hour"
```

**File:** `apps/api/plane/throttles/asset.py`

```python
from plane.license.utils.instance_value import get_configuration_value

class AssetRateThrottle(SimpleRateThrottle):
    scope = "asset_id"

    @property
    def rate(self):
        (rate_limit,) = get_configuration_value([
            {"key": "RATE_LIMIT_ASSET", "default": "5/minute"}
        ])
        return rate_limit or "5/minute"
```

#### 1.3 Update REST Framework Default Settings

**File:** `apps/api/plane/settings/common.py`

The anonymous throttle rate needs to be dynamic. Consider creating a custom throttle class or updating the setting dynamically.

### Phase 2: Frontend Types (Priority: High)

#### 2.1 Add Rate Limit Type Definitions

**File:** `packages/types/src/instance/rate-limit.ts` (new file)

```typescript
export type TInstanceRateLimitConfigurationKeys =
  | "RATE_LIMIT_API_KEY"
  | "RATE_LIMIT_SERVICE_TOKEN"
  | "RATE_LIMIT_AUTHENTICATION"
  | "RATE_LIMIT_EMAIL_VERIFICATION"
  | "RATE_LIMIT_ASSET"
  | "RATE_LIMIT_ANONYMOUS";

export interface IRateLimitConfiguration {
  RATE_LIMIT_API_KEY: string;
  RATE_LIMIT_SERVICE_TOKEN: string;
  RATE_LIMIT_AUTHENTICATION: string;
  RATE_LIMIT_EMAIL_VERIFICATION: string;
  RATE_LIMIT_ASSET: string;
  RATE_LIMIT_ANONYMOUS: string;
}
```

**File:** `packages/types/src/instance/index.ts`

```typescript
export * from "./rate-limit";
```

**File:** `packages/types/src/instance/base.ts`

Update `TInstanceConfigurationKeys` to include rate limit keys.

### Phase 3: Admin Panel UI (Priority: High)

#### 3.1 Add Sidebar Menu Item

**File:** `apps/admin/app/(all)/(dashboard)/sidebar-menu.tsx`

```typescript
import { Gauge } from "lucide-react";

const INSTANCE_ADMIN_LINKS = [
  // ... existing items
  {
    Icon: Gauge,
    name: "Rate Limits",
    description: "Configure API rate limiting.",
    href: `/rate-limits/`,
  },
];
```

#### 3.2 Create Rate Limits Page

**File:** `apps/admin/app/(all)/(dashboard)/rate-limits/page.tsx` (new)

```typescript
import { observer } from "mobx-react";
import { useInstance } from "@/hooks/store";
import type { Route } from "./+types/page";
import { RateLimitsConfigurationForm } from "./form";

function RateLimitsPage() {
  const { formattedConfig } = useInstance();

  return (
    <div className="relative container mx-auto w-full h-full p-4 py-4 space-y-6 flex flex-col">
      <div className="border-b border-custom-border-100 mx-4 py-4 space-y-1 flex-shrink-0">
        <div className="text-xl font-medium text-custom-text-100">Rate Limits</div>
        <div className="text-sm font-normal text-custom-text-300">
          Configure API rate limiting for your instance. Rate limits help protect your instance from abuse.
        </div>
      </div>
      <div className="flex-grow overflow-hidden overflow-y-scroll vertical-scrollbar scrollbar-md px-4">
        {formattedConfig && <RateLimitsConfigurationForm config={formattedConfig} />}
      </div>
    </div>
  );
}

export const meta: Route.MetaFunction = () => [{ title: "Rate Limits - God Mode" }];

export default observer(RateLimitsPage);
```

#### 3.3 Create Rate Limits Form

**File:** `apps/admin/app/(all)/(dashboard)/rate-limits/form.tsx` (new)

```typescript
import { observer } from "mobx-react";
import { useForm } from "react-hook-form";
import { Gauge, Shield, Mail, Image, Users, Globe } from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IFormattedInstanceConfiguration } from "@plane/types";
import { ControllerInput } from "@/components/common/controller-input";
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
    key: "RATE_LIMIT_API_KEY",
    label: "API Key Rate Limit",
    description: "Rate limit for authenticated API requests using API keys",
    icon: Gauge,
    placeholder: "60/minute",
    helpText: "Format: number/period (e.g., 60/minute, 1000/hour, 10000/day)",
  },
  {
    key: "RATE_LIMIT_SERVICE_TOKEN",
    label: "Service Token Rate Limit",
    description: "Rate limit for service-to-service API requests",
    icon: Shield,
    placeholder: "300/minute",
    helpText: "Higher limit for automated service integrations",
  },
  {
    key: "RATE_LIMIT_AUTHENTICATION",
    label: "Authentication Rate Limit",
    description: "Rate limit for login, signup, and password reset endpoints",
    icon: Users,
    placeholder: "30/minute",
    helpText: "Protects against brute-force attacks",
  },
  {
    key: "RATE_LIMIT_EMAIL_VERIFICATION",
    label: "Email Verification Rate Limit",
    description: "Rate limit for email verification code generation",
    icon: Mail,
    placeholder: "3/hour",
    helpText: "Prevents email spam abuse",
  },
  {
    key: "RATE_LIMIT_ASSET",
    label: "Asset Upload Rate Limit",
    description: "Rate limit for file uploads per asset",
    icon: Image,
    placeholder: "5/minute",
    helpText: "Per-asset rate limiting",
  },
  {
    key: "RATE_LIMIT_ANONYMOUS",
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
          message: `${key} must be in format: number/period (e.g., 60/minute)`,
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
      <div className="bg-amber-500/10 border border-amber-500/20 rounded-md p-4">
        <div className="text-sm text-amber-600">
          <strong>Note:</strong> Rate limit changes may take up to 2 hours to take effect due to caching.
          Setting very high limits may impact instance performance and security.
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
                    name={field.key as keyof IRateLimitsForm}
                    control={control}
                    type="text"
                    placeholder={field.placeholder}
                    error={Boolean(errors[field.key as keyof IRateLimitsForm])}
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
```

### Phase 4: Testing

1. **Backend Unit Tests:**
   - Test that throttle classes correctly read from instance configuration
   - Test fallback to environment variables when config is not set
   - Test rate limit parsing (number/period format)

2. **Frontend Tests:**
   - Test form validation for rate limit format
   - Test configuration updates via API

3. **Integration Tests:**
   - Verify rate limits are applied correctly after configuration change
   - Test cache invalidation timing

## File Changes Summary

### New Files
- `packages/types/src/instance/rate-limit.ts`
- `apps/admin/app/(all)/(dashboard)/rate-limits/page.tsx`
- `apps/admin/app/(all)/(dashboard)/rate-limits/form.tsx`

### Modified Files
- `apps/api/plane/utils/instance_config_variables/core.py` - Add rate limit variables
- `apps/api/plane/api/rate_limit.py` - Use dynamic configuration
- `apps/api/plane/authentication/rate_limit.py` - Use dynamic configuration
- `apps/api/plane/throttles/asset.py` - Use dynamic configuration
- `packages/types/src/instance/index.ts` - Export rate limit types
- `packages/types/src/instance/base.ts` - Add rate limit keys to union type
- `apps/admin/app/(all)/(dashboard)/sidebar-menu.tsx` - Add menu item

## Security Considerations

1. Only instance admins can modify rate limits (enforced by `InstanceAdminPermission`)
2. Rate limit values are not encrypted (they're not sensitive)
3. Validation prevents invalid rate limit formats
4. Minimum rate limits could be enforced to prevent denial of service to legitimate users

## Rollback Plan

If issues arise:
1. Set configuration values back to defaults via admin panel
2. Or delete the `InstanceConfiguration` entries for rate limit keys
3. System will fall back to environment variables or hardcoded defaults

## Migration Notes

- Existing instances will use default values until explicitly configured
- No database migration required (uses existing `InstanceConfiguration` model)
- Backward compatible with current environment variable approach
