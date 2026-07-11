import { LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function KpiCard({
  title,
  value,
  icon: Icon,
  note,
}: {
  title: string;
  value: string | number;
  icon: LucideIcon;
  note?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-slate-400">{title}</CardTitle>
        <Icon size={17} className="text-accent" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold text-slate-50">{value}</div>
        {note ? <div className="mt-1 text-xs text-slate-500">{note}</div> : null}
      </CardContent>
    </Card>
  );
}
