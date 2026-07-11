"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Download, Play, Timer } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export default function CallDetailsPage() {
  const params = useParams<{ id: string }>();
  const { data, isLoading } = useQuery({ queryKey: ["call-details", params.id], queryFn: () => apiFetch<any>(`/admin/call-details/${params.id}`) });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Call Details" description="Transcript, summary, recording, timeline, provider usage, latency, and cost placeholder." />
      <div className="grid gap-3 xl:grid-cols-[1.4fr_.9fr]">
        <Card>
          <CardHeader><CardTitle>Transcript</CardTitle><Badge>{data.call.language_detection}</Badge></CardHeader>
          <CardContent className="space-y-3">
            {data.transcript.map((turn: any, index: number) => (
              <div key={index} className={turn.speaker === "assistant" ? "ml-auto max-w-[85%] rounded-lg border border-teal-500/20 bg-teal-500/10 p-3" : "max-w-[85%] rounded-lg border border-border bg-slate-950 p-3"}>
                <div className="mb-1 flex items-center justify-between gap-3 text-xs text-slate-500">
                  <span>{turn.speaker === "assistant" ? "AI" : "Customer"}</span>
                  <span>{turn.language} · {turn.timestamp}</span>
                </div>
                <p className="text-sm text-slate-100">{turn.text}</p>
              </div>
            ))}
            {data.transcript.length === 0 ? <div className="text-sm text-slate-500">No transcript turns captured yet.</div> : null}
          </CardContent>
        </Card>
        <div className="space-y-3">
          <Card>
            <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-300">
              <p>{data.summary ?? "Summary will appear after the call ends."}</p>
              <div><span className="text-slate-500">Topics:</span> {data.topics.length ? data.topics.join(", ") : "placeholder"}</div>
              <div><span className="text-slate-500">Action Items:</span> {data.action_items.length ? data.action_items.join(", ") : "placeholder"}</div>
              <div><span className="text-slate-500">Sentiment:</span> {data.sentiment}</div>
              <div><span className="text-slate-500">Estimated Cost:</span> {data.call.estimated_cost}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Recording</CardTitle></CardHeader>
            <CardContent className="flex gap-2">
              <Button variant="ghost"><Play size={15} />Playback</Button>
              <Button variant="ghost"><Download size={15} />Download</Button>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle>Timeline</CardTitle><Timer size={17} className="text-accent" /></CardHeader>
            <CardContent className="space-y-2">
              {data.timeline.map((event: any, index: number) => (
                <div key={index} className="rounded-md border border-border bg-slate-950 p-2 text-xs text-slate-400">
                  <div className="text-slate-200">{event.type}</div>
                  <div>{event.time}</div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
