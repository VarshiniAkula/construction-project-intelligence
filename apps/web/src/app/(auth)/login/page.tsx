"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { HardHat } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md">
      <div className="text-center mb-8">
        <div className="w-14 h-14 bg-hard-hat rounded-2xl flex items-center justify-center mx-auto mb-4">
          <HardHat className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-white">Sign in to Construction RAG</h1>
        <p className="text-gray-400 mt-1">Construction Project Intelligence</p>
      </div>

      <form onSubmit={handleSubmit} className="card p-8 space-y-5">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-hard-slate mb-1.5">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="input-field"
            placeholder="you@company.com"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-hard-slate mb-1.5">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input-field"
            placeholder="Enter your password"
            required
          />
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full py-2.5">
          {loading ? "Signing in..." : "Sign In"}
        </button>

        <p className="text-center text-sm text-hard-concrete pt-2">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-hard-hat hover:text-orange-400 font-medium">
            Create one
          </Link>
        </p>
      </form>
    </div>
  );
}
