"use client";
import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import { usePathname } from "next/navigation";

import { AuthProvider } from "@/context/auth-context";
import ProtectedRoute from "@/components/auth/ProtectedRoute";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  if (isLoginPage) {
    return (
      <html lang="en">
        <body>
          <AuthProvider>
            <div className="glow-bg" />
            {children}
          </AuthProvider>
        </body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <ProtectedRoute>
            <div className="glow-bg" />
            <div className="layout-root">
              <Sidebar />
              <div className="main-container">
                <TopBar />
                <main className="content-scroll">
                  {children}
                </main>
              </div>
            </div>
          </ProtectedRoute>
        </AuthProvider>
      </body>
    </html>
  );
}

