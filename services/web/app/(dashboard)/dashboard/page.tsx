"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Bot, CheckCircle2, Clock, Cpu, Database, Gauge, PhoneCall, Radio, XCircle } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { PageHeader } from "@/components/dashboard/page-header";
import { KpiCard } from "@/components/dashboard/kpi-card";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { DashboardOverview } from "@/types/api";

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch<DashboardOverview>("/admin/dashboard"),
  });

  if (isLoading || !data) return <LoadingState />;
  const providerData = Object.entries(data.provider_usage).map(([name, value]) => ({ name, value }));
  const kpis = data.kpis;

  return (
    <>
      <PageHeader title="Dashboard" description="Real-time operating view for the Bangla-first AI voice platform." />
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard title="Active Calls" value={kpis.active_calls} icon={PhoneCall} note="Live sessions now" />
        <KpiCard title="Today's Calls" value={kpis.todays_calls} icon={Activity} note="Since local midnight" />
        <KpiCard title="Total Calls" value={kpis.total_calls} icon={Radio} note="All tenants" />
        <KpiCard title="Avg Duration" value={`${kpis.average_duration_seconds}s`} icon={Clock} note="Placeholder until call end events mature" />
        <KpiCard title="Avg Latency" value={`${kpis.average_latency_ms}ms`} icon={Gauge} note="STT + LLM + TTS average" />
        <KpiCard title="Success Rate" value={`${kpis.success_rate}%`} icon={CheckCircle2} note="Completed vs total" />
        <KpiCard title="Failed Calls" value={kpis.failed_calls} icon={XCircle} note="Needs attention" />
        <KpiCard title="Live Sessions" value={kpis.live_sessions} icon={Bot} note="Redis-backed active state" />
      </div>
      <div className="mt-3 grid gap-3 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>System Status</CardTitle>
            <Cpu size={17} className="text-accent" />
          </CardHeader>
          <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(data.system_status).map(([name, status]) => (
              <div key={name} className="flex items-center justify-between rounded-md border border-border bg-slate-950 px-3 py-2">
                <span className="text-sm capitalize text-slate-300">{name.replaceAll("_", " ")}</span>
                <Badge className={status === "healthy" ? "border-teal-500/40 text-teal-300" : "text-slate-400"}>{status}</Badge>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Provider Usage</CardTitle>
            <Database size={17} className="text-accent" />
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={providerData.length ? providerData : [{ name: "No calls yet", value: 1 }]} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82}>
                  {(providerData.length ? providerData : [{ name: "No calls yet", value: 1 }]).map((_, index) => (
                    <Cell key={index} fill={["#2dd4bf", "#60a5fa", "#a78bfa", "#f59e0b"][index % 4]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #253042" }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
      <Card className="mt-3">
        <CardHeader>
          <CardTitle>Roadmap</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-2 xl:grid-cols-5">
          {data.roadmap.map((item) => <Badge key={item}>{item}</Badge>)}
        </CardContent>
      </Card>
    </>
  );
}
