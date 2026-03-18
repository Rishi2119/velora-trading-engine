"use client";

import { useAuth } from "@/context/auth-context";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user && pathname !== "/login") {
      router.replace("/login");
    }
  }, [user, loading, router, pathname]);

  if (loading) {
    return (
      <div className="flex-center" style={{ height: "100vh", flexDirection: "column", gap: "1rem" }}>
        <RefreshCw className="spin text-cyan" size={32} />
        <span className="text-muted" style={{ fontSize: "10px", letterSpacing: "2px" }}>VERIFYING_HANDSHAKE...</span>
      </div>
    );
  }

  if (!user && pathname !== "/login") {
    return null;
  }

  return <>{children}</>;
}
