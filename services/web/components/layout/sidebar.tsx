"use client";

import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  Clock,
  Database,
  History,
  LayoutDashboard,
  ListTree,
  PhoneCall,
  Settings,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/live-calls", label: "Live Calls", icon: PhoneCall },
  { href: "/calls", label: "Call History", icon: History },
  { href: "/customers", label: "Customers", icon: Users },
  { href: "/campaigns", label: "Campaigns", icon: ListTree },
  { href: "/knowledge-base", label: "Knowledge Base", icon: BookOpen },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/providers", label: "Providers", icon: Bot },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/logs", label: "Logs", icon: Clock },
  { href: "/system", label: "System", icon: Database },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-slate-950/70 px-3 py-4 lg:block">
      <Link href="/dashboard" className="mb-6 flex items-center gap-3 px-2">
        <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-slate-950">
          <Activity size={19} />
        </div>
        <div>
          <div className="text-sm font-semibold">VoxAgent</div>
          <div className="text-xs text-muted">Voice SaaS MVP</div>
        </div>
      </Link>
      <nav className="space-y-1">
        {nav.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex h-9 items-center gap-3 rounded-md px-2 text-sm text-slate-400 hover:bg-white/5 hover:text-slate-100",
                active && "bg-white/10 text-slate-100",
              )}
            >
              <Icon size={17} />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
