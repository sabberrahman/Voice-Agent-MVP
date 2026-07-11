"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, CircleAlert } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export default function SystemPage() {
  const { data, isLoading } = useQuery({ queryKey: ["system"], queryFn: () => apiFetch<{ services: any[] }>("/admin/system") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="System" description="Health dashboard for core local services and future observability surfaces." />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {data.services.map((service) => {
          const healthy = ["healthy", "configured", "local"].includes(service.status);
          const Icon = healthy ? CheckCircle2 : CircleAlert;
          return (
            <Card key={service.name}>
              <CardContent className="flex items-start justify-between gap-3 pt-4">
                <div>
                  <div className="font-medium text-slate-100">{service.name}</div>
                  <div className="mt-1 text-sm text-slate-500">{service.detail}</div>
                </div>
                <div className="flex items-center gap-2"><Icon size={16} className={healthy ? "text-accent" : "text-amber-400"} /><Badge>{service.status}</Badge></div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </>
  );
}
