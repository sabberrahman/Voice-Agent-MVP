"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/dashboard/page-header";
import { LoadingState } from "@/components/dashboard/loading";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";

export default function CustomersPage() {
  const { data, isLoading } = useQuery({ queryKey: ["customers"], queryFn: () => apiFetch<{ items: any[] }>("/admin/customers") });
  if (isLoading || !data) return <LoadingState />;
  return (
    <>
      <PageHeader title="Customers" description="Customer records prepared for CRM integration and tenant isolation." />
      <Card>
        <CardContent className="overflow-x-auto pt-4">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-500"><tr><th>Name</th><th>Phone</th><th>Company</th><th>Last Call</th><th>Total Calls</th><th>Language</th><th>Notes</th></tr></thead>
            <tbody>
              {data.items.map((customer) => (
                <tr key={customer.id} className="border-t border-border">
                  <td className="py-3">{customer.name ?? "Unknown"}</td><td>{customer.phone ?? "-"}</td><td>{customer.company ?? "-"}</td><td>{customer.last_call ?? "-"}</td><td>{customer.total_calls}</td><td><Badge>{customer.preferred_language}</Badge></td><td>{customer.notes ?? "Future CRM placeholder"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.items.length === 0 ? <div className="py-8 text-center text-sm text-slate-500">No customers yet. Future CRM sync is ready as a placeholder.</div> : null}
        </CardContent>
      </Card>
    </>
  );
}
