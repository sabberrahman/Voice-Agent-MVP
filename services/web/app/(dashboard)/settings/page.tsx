"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export default function SettingsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["settings"], queryFn: () => apiFetch<any>("/admin/settings") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Settings" description="Environment, providers, voice, language, timeout, retry, recording, prompts, and future tenant settings." />
      <div className="grid gap-3 xl:grid-cols-2">
        {Object.entries(data).map(([section, value]) => (
          <Card key={section}>
            <CardHeader><CardTitle className="capitalize">{section.replaceAll("_", " ")}</CardTitle></CardHeader>
            <CardContent className="flex flex-wrap gap-2 text-sm text-slate-300">
              {typeof value === "object" && value !== null
                ? Object.entries(value as Record<string, any>).map(([key, item]) => <Badge key={key}>{key}: {Array.isArray(item) ? item.join(", ") : String(item)}</Badge>)
                : <Badge>{String(value)}</Badge>}
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
