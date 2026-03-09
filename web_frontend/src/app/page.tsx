"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { Shield } from "lucide-react";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    if (auth.isLoggedIn()) {
      router.replace("/dashboard");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div className="flex-center" style={{ height: "100vh", flexDirection: "column", gap: 16 }}>
      <Shield size={40} color="#6366f1" />
      <p className="text-muted">Loading Velora…</p>
    </div>
  );
}
