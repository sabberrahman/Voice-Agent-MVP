"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@voxagent.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await login(email, password);
      window.localStorage.setItem("voxagent_token", response.access_token);
      router.push("/dashboard");
    } catch {
      setError("Login failed. Check the demo credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-accent text-slate-950">
              <Activity size={18} />
            </div>
            <div>
              <CardTitle>VoxAgent</CardTitle>
              <p className="text-xs text-slate-500">Internal admin console</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-3" onSubmit={submit}>
            <Input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
            <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
            {error ? <p className="text-sm text-danger">{error}</p> : null}
            <Button className="w-full" disabled={loading}>{loading ? "Signing in..." : "Login"}</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
