"use client";

import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

function ChartCard({ title, data, type = "bar" }: { title: string; data: any[]; type?: "bar" | "line" }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          {type === "line" ? (
            <LineChart data={data}><CartesianGrid stroke="#1f2937" /><XAxis dataKey="name" stroke="#64748b" /><YAxis stroke="#64748b" /><Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #253042" }} /><Line type="monotone" dataKey="value" stroke="#2dd4bf" strokeWidth={2} /></LineChart>
          ) : (
            <BarChart data={data}><CartesianGrid stroke="#1f2937" /><XAxis dataKey="name" stroke="#64748b" /><YAxis stroke="#64748b" /><Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #253042" }} /><Bar dataKey="value" fill="#2dd4bf" radius={[4, 4, 0, 0]} /></BarChart>
          )}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["analytics"], queryFn: () => apiFetch<any>("/admin/analytics") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Analytics" description="Call volume, language usage, provider usage, success rate, latency, and conversation length." />
      <div className="grid gap-3 xl:grid-cols-2">
        <ChartCard title="Calls Per Day" data={data.calls_per_day} type="line" />
        <ChartCard title="Calls Per Hour" data={data.calls_per_hour} />
        <ChartCard title="Languages Used" data={data.languages_used} />
        <ChartCard title="Provider Usage" data={data.provider_usage} />
      </div>
    </>
  );
}
