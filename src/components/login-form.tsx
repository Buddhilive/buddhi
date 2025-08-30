"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

type FormData = {
  username: string;
  password: string;
};

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"form">) {
  const [formData, setFormData] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      // Use client-side fetch instead of server action
      const body = new URLSearchParams();
      body.append("username", formData.username);
      body.append("password", formData.password);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
        credentials: "include",
      });
      
      const data = await response.json();
      console.log("=== LOGIN DEBUG ===");
      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);
      console.log("Response data:", data);
      console.log("All response headers:");
      for (let [key, value] of response.headers.entries()) {
        console.log(`  ${key}: ${value}`);
      }
      console.log("==================");
      
      if (response.ok) {
        console.log("Login successful, redirecting to dashboard");
        console.log("Document cookies after login:", document.cookie);
        // Wait a bit for cookies to be set
        setTimeout(() => {
          console.log("Document cookies after timeout:", document.cookie);
          router.push("/dashboard");
        }, 100);
      } else {
        setError(data?.detail || "Login failed");
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Network error occurred");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("flex flex-col gap-6", className)}
      {...props}
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Login to your account</h1>
        <p className="text-muted-foreground text-sm text-balance">
          Enter your email below to login to your account
        </p>
      </div>
      <div className="grid gap-6">
        <div className="grid gap-3">
          <Label htmlFor="username">Username</Label>
          <Input
            id="username"
            type="text"
            placeholder="your username"
            value={formData.username}
            onChange={(e) =>
              setFormData({ ...formData, username: e.target.value })
            }
          />
        </div>
        <div className="grid gap-3">
          <div className="flex items-center">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/forgot-password"
              className="ml-auto text-sm underline-offset-4 hover:underline"
            >
              Forgot your password?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            value={formData.password}
            onChange={(e) =>
              setFormData({ ...formData, password: e.target.value })
            }
          />
        </div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </Button>
      </div>
      <div className="text-center">
        <span className="text-gray-600">Don't have an account? </span>
        <Link href="/register" className="text-blue-600 hover:text-blue-500">
          Sign up
        </Link>
      </div>
    </form>
  );
}
