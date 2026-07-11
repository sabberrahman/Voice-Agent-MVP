"use client";

import { useQuery } from "@tanstack/react-query";
import { MicOff, PhoneOff, Shuffle } from "lucide-react";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export default function LiveCallsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["live-calls"], queryFn: () => apiFetch<{ items: any[] }>("/admin/live-calls") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Live Calls" description="Active AI conversations, current transcript, response, provider, and call controls." />
      <div className="space-y-3">
        {data.items.length === 0 ? <Card><CardContent className="pt-4 text-sm text-slate-400">No active calls. Start a Zoiper session to see live state here.</CardContent></Card> : null}
        {data.items.map((call) => (
          <Card key={call.session_id}>
            <CardContent className="grid gap-4 pt-4 xl:grid-cols-[1fr_1.5fr_1.5fr_auto]">
              <div>
                <div className="text-sm font-medium">{call.caller}</div>
                <div className="mt-1 text-xs text-slate-500">{call.call_id}</div>
                <div className="mt-3 flex gap-2"><Badge>{call.language}</Badge><Badge>{call.call_status}</Badge><Badge>{call.audio_streaming_status}</Badge></div>
              </div>
              <div>
                <div className="text-xs text-slate-500">Current Transcript</div>
                <p className="mt-1 text-sm text-slate-200">{call.current_transcript ?? "Listening..."}</p>
              </div>
              <div>
                <div className="text-xs text-slate-500">AI Response</div>
                <p className="mt-1 text-sm text-slate-200">{call.ai_response ?? "Waiting for model response..."}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="danger"><PhoneOff size={15} />End</Button>
                <Button variant="ghost"><Shuffle size={15} />Transfer</Button>
                <Button variant="ghost"><MicOff size={15} />Mute</Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </>
  );
}
