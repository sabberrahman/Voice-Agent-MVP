"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api";

export default function CallsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["calls"], queryFn: () => apiFetch<{ items: any[]; next_cursor?: string | null }>("/calls") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Call History" description="Searchable call records with status, duration, language, providers, transcripts, and recordings." />
      <div className="mb-3 grid gap-2 md:grid-cols-[1fr_auto_auto_auto]">
        <div className="relative">
          <Search className="absolute left-3 top-3 text-slate-500" size={15} />
          <Input className="pl-9" placeholder="Search by customer, phone, language, status" />
        </div>
        <Input placeholder="Date filter" />
        <Input placeholder="Customer filter" />
        <Input placeholder="Status filter" />
      </div>
      <Card>
        <CardContent className="overflow-x-auto pt-4">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-500">
              <tr><th className="py-2">Call</th><th>Status</th><th>Language</th><th>Started</th><th>Ended</th><th>Recording</th></tr>
            </thead>
            <tbody>
              {data.items.map((call) => (
                <tr key={call.id} className="border-t border-border">
                  <td className="py-3"><Link className="text-accent hover:underline" href={`/calls/${call.id}`}>{call.id}</Link></td>
                  <td><Badge>{call.status}</Badge></td>
                  <td>{call.language ?? "bn-BD"}</td>
                  <td className="text-slate-400">{call.started_at ?? "-"}</td>
                  <td className="text-slate-400">{call.ended_at ?? "-"}</td>
                  <td><Badge>{call.recording_status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.items.length === 0 ? <div className="py-8 text-center text-sm text-slate-500">No calls yet.</div> : null}
          <div className="mt-4 text-xs text-slate-500">Pagination placeholder: next cursor {String(data.next_cursor ?? "none")}</div>
        </CardContent>
      </Card>
    </>
  );
}
