import { observer } from "mobx-react";
import useSWR from "swr";
import { Loader } from "@plane/ui";
// hooks
import { useInstance } from "@/hooks/store";
// components
import type { Route } from "./+types/page";
import { RateLimitsConfigurationForm } from "./form";

const RateLimitsPage = observer(function RateLimitsPage(_props: Route.ComponentProps) {
  // store
  const { fetchInstanceConfigurations, formattedConfig } = useInstance();

  useSWR("INSTANCE_CONFIGURATIONS", () => fetchInstanceConfigurations());

  return (
    <>
      <div className="relative container mx-auto w-full h-full p-4 py-4 space-y-6 flex flex-col">
        <div className="border-b border-custom-border-100 mx-4 py-4 space-y-1 flex-shrink-0">
          <div className="text-xl font-medium text-custom-text-100">Rate Limits</div>
          <div className="text-sm font-normal text-custom-text-300">
            Configure API rate limiting for your instance. Rate limits help protect your instance from abuse and ensure
            fair usage.
          </div>
        </div>
        <div className="flex-grow overflow-hidden overflow-y-scroll vertical-scrollbar scrollbar-md px-4">
          {formattedConfig ? (
            <RateLimitsConfigurationForm config={formattedConfig} />
          ) : (
            <Loader className="space-y-8">
              <Loader.Item height="50px" width="100%" />
              <Loader.Item height="100px" width="100%" />
              <Loader.Item height="100px" width="100%" />
              <Loader.Item height="100px" width="100%" />
            </Loader>
          )}
        </div>
      </div>
    </>
  );
});

export const meta: Route.MetaFunction = () => [{ title: "Rate Limits - God Mode" }];

export default RateLimitsPage;
