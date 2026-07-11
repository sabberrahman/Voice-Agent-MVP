"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export function SimpleAdminPage({ title, description, endpoint }: { title: string; description: string; endpoint: string }) {
  const { data, isLoading } = useQuery({ queryKey: [endpoint], queryFn: () => apiFetch<any>(endpoint) });
  if (isLoading || !data) return <LoadingState />;
  const placeholders = data.placeholders ?? data.items?.map((item: any) => item.message ?? item.name ?? JSON.stringify(item)) ?? [];
  return (
    <>
      <PageHeader title={title} description={description} />
      <Card>
        <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {placeholders.length ? placeholders.map((item: string) => <Badge key={item}>{item}</Badge>) : <span className="text-sm text-slate-500">No records yet.</span>}
        </CardContent>
      </Card>
    </>
  );
}
