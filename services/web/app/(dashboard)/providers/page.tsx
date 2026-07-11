"use client";

import { useQuery } from "@tanstack/react-query";
import { Bot } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export default function ProvidersPage() {
  const { data, isLoading } = useQuery({ queryKey: ["providers-admin"], queryFn: () => apiFetch<any>("/admin/providers") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Providers" description="Provider-agnostic STT, LLM, and TTS configuration with future switching controls." />
      <div className="grid gap-3 xl:grid-cols-3">
        {data.items.map((item: any) => (
          <Card key={item.type}>
            <CardHeader><CardTitle>{item.type}</CardTitle><Bot size={17} className="text-accent" /></CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Active Provider</span><Badge>{item.active_provider}</Badge></div>
              <div className="flex justify-between"><span className="text-slate-500">Status</span><span>{item.status}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Health</span><span>{item.health}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Avg Latency</span><span>{item.latency_ms} ms</span></div>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="mt-3">
        <CardHeader><CardTitle>Available Providers</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          {Object.entries(data.available).map(([kind, providers]) => (
            <div key={kind} className="space-y-2">
              <div className="text-sm font-medium uppercase text-slate-400">{kind}</div>
              <div className="flex flex-wrap gap-2">{(providers as string[]).map((provider) => <Badge key={provider}>{provider}</Badge>)}</div>
            </div>
          ))}
        </CardContent>
      </Card>
    </>
  );
}
