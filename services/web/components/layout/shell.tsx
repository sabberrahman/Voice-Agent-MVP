import { Sidebar } from "@/components/layout/sidebar";
import { AuthGuard } from "@/components/layout/auth-guard";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-background">
        <Sidebar />
        <main className="lg:pl-64">
          <div className="mx-auto w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">{children}</div>
        </main>
      </div>
    </AuthGuard>
  );
}
