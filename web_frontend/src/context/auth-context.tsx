"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { 
  User, 
  onAuthStateChanged, 
  signInWithPopup, 
  GoogleAuthProvider, 
  signOut as firebaseSignOut 
} from "firebase/auth";
import { auth as firebaseAuth } from "@/lib/firebase";

import { supabase } from "@/lib/supabase";
import { useRouter } from "next/navigation";

const IS_FIREBASE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_FIREBASE === "true";

interface AuthUser {
  id: string;
  email: string | undefined;
  displayName: string | null | undefined;
  photoURL: string | null | undefined;
  provider: string;
}

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let unsubscribe: () => void = () => {};

    if (IS_FIREBASE_ENABLED) {
      unsubscribe = onAuthStateChanged(firebaseAuth, async (firebaseUser) => {
        if (firebaseUser) {
          try {
            const idToken = await firebaseUser.getIdToken();
            const synced = await syncWithBackend(idToken, "firebase");
            if (synced) {
              setUser({
                id: firebaseUser.uid,
                email: firebaseUser.email || undefined,
                displayName: firebaseUser.displayName,
                photoURL: firebaseUser.photoURL,
                provider: "firebase",
              });
            } else {
              await firebaseSignOut(firebaseAuth);
              setUser(null);
            }
          } catch (error) {
            console.error("Firebase Auth Sync Error:", error);
            setUser(null);
          }
        } else {
          setUser(null);
          clearStorage();
        }
        setLoading(false);
      });
    } else {
      // Supabase listener
      const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
        if (session?.user) {
          try {
            // In a real app, you'd sync with backend here too if needed
            // For now, let's just set the user
            setUser({
              id: session.user.id,
              email: session.user.email,
              displayName: session.user.user_metadata.full_name || session.user.email,
              photoURL: session.user.user_metadata.avatar_url,
              provider: "supabase",
            });
            
            // Minimal backend sync for Supabase (can be expanded)
            localStorage.setItem("velora_token", session.access_token);
            localStorage.setItem("velora_user", JSON.stringify({
              id: session.user.id,
              email: session.user.email,
              displayName: session.user.user_metadata.full_name,
            }));

          } catch (error) {
            console.error("Supabase Auth Sync Error:", error);
            setUser(null);
          }
        } else {
          setUser(null);
          clearStorage();
        }
        setLoading(false);
      });

      unsubscribe = () => subscription.unsubscribe();
    }

    return () => unsubscribe();
  }, []);

  const syncWithBackend = async (idToken: string, provider: "firebase" | "supabase") => {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
      const endpoint = provider === "firebase" ? "/auth/firebase-login" : "/auth/supabase-login";
      
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id_token: idToken }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("velora_token", data.access_token);
        localStorage.setItem("velora_user", JSON.stringify({
          id: data.user_id,
          email: data.email,
        }));
        return true;
      }
      return false;
    } catch (error) {
      console.error("Backend sync failed:", error);
      return false;
    }
  };

  const clearStorage = () => {
    localStorage.removeItem("velora_token");
    localStorage.removeItem("velora_user");
  };

  const signInWithGoogle = async () => {
    try {
      if (IS_FIREBASE_ENABLED) {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(firebaseAuth, provider);
        const idToken = await result.user.getIdToken();
        const synced = await syncWithBackend(idToken, "firebase");
        if (!synced) throw new Error("Backend synchronization failed");
      } else {
        const { error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: {
            redirectTo: window.location.origin + '/dashboard'
          }
        });
        if (error) throw error;
      }
      
      router.push("/dashboard");
    } catch (error) {
      console.error("Google Sign-In Error:", error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (IS_FIREBASE_ENABLED) {
        await firebaseSignOut(firebaseAuth);
      } else {
        await supabase.auth.signOut();
      }
      clearStorage();
      router.push("/login");
    } catch (error) {
      console.error("Logout Error:", error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
}


export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
