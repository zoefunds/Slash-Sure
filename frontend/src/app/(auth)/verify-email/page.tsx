"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle, XCircle, Loader2, Shield } from "lucide-react";
import Link from "next/link";
import { authApi } from "@/lib/api";

function VerifyEmailContent() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token found.");
      return;
    }
    authApi.verifyEmail(token)
      .then(({ data }) => {
        setStatus("success");
        setMessage(data.message || "Email verified!");
        setTimeout(() => router.push("/dashboard"), 3000);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err?.response?.data?.detail || "Verification failed or link expired.");
      });
  }, [token, router]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center space-y-6">
        <div className="flex items-center justify-center gap-2 mb-8">
          <Shield className="w-8 h-8 text-blue-400" />
          <span className="text-2xl font-bold">
            <span className="text-blue-400">Slash</span>Sure
          </span>
        </div>

        {status === "loading" && (
          <div className="p-8 rounded-2xl border border-border bg-card space-y-4">
            <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto" />
            <p className="text-muted-foreground">Verifying your email…</p>
          </div>
        )}

        {status === "success" && (
          <div className="p-8 rounded-2xl border border-green-500/20 bg-card space-y-4">
            <CheckCircle className="w-12 h-12 text-green-400 mx-auto" />
            <h2 className="text-xl font-bold text-white">Email Verified!</h2>
            <p className="text-muted-foreground">{message}</p>
            <p className="text-sm text-muted-foreground">Redirecting to dashboard…</p>
          </div>
        )}

        {status === "error" && (
          <div className="p-8 rounded-2xl border border-red-500/20 bg-card space-y-4">
            <XCircle className="w-12 h-12 text-red-400 mx-auto" />
            <h2 className="text-xl font-bold text-white">Verification Failed</h2>
            <p className="text-muted-foreground">{message}</p>
            <Link
              href="/login"
              className="inline-block mt-4 text-blue-400 hover:underline text-sm"
            >
              Back to login
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-400" /></div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
