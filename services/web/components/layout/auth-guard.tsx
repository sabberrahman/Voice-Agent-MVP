"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { getToken } from "@/lib/api";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (!getToken() && pathname !== "/login") {
      router.replace("/login");
    }
  }, [pathname, router]);
  return <>{children}</>;
}
