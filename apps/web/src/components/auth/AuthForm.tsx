"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Input } from "@ks-ai/ui";
import { useAuthStore } from "@/lib/state/useAuthStore";
import { authAPI } from "@/lib/api/auth";

interface AuthFormProps {
  mode: "login" | "register";
  onToggleMode: () => void;
}

export function AuthForm({ mode, onToggleMode }: AuthFormProps) {
  const router = useRouter();
  const { login, setLoading, isLoading } = useAuthStore();
  const [formData, setFormData] = useState({
    email: "",
    phoneNumber: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(""); // Clear error when user starts typing
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        // Validate passwords match
        if (formData.password !== formData.confirmPassword) {
          setError("Passwords do not match");
          setLoading(false);
          return;
        }

        // Validate at least email or phone is provided
        if (!formData.email && !formData.phoneNumber) {
          setError("Please provide either email or phone number");
          setLoading(false);
          return;
        }

        // Register user
        const user = await authAPI.register({
          email: formData.email || undefined,
          phoneNumber: formData.phoneNumber || undefined,
          password: formData.password,
        });

        // Auto-login after registration
        const tokenResponse = await authAPI.login({
          username: formData.email || formData.phoneNumber,
          password: formData.password,
        });

        login(user, tokenResponse.accessToken);
        router.push("/");
      } else {
        // Login
        const username = formData.email || formData.phoneNumber;
        if (!username) {
          setError("Please provide email or phone number");
          setLoading(false);
          return;
        }

        const tokenResponse = await authAPI.login({
          username,
          password: formData.password,
        });

        // Get user info
        const user = await authAPI.getCurrentUser(tokenResponse.accessToken);
        
        login(user, tokenResponse.accessToken);
        router.push("/");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">
          {mode === "login" ? "Welcome Back" : "Create Account"}
        </h1>
        <p className="text-muted-foreground">
          {mode === "login"
            ? "Sign in to your account"
            : "Sign up to get started"}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email"
          type="email"
          placeholder="your@email.com"
          value={formData.email}
          onChange={(e) => handleInputChange("email", e.target.value)}
        />

        <Input
          label="Phone Number (Optional)"
          type="tel"
          placeholder="+1234567890"
          value={formData.phoneNumber}
          onChange={(e) => handleInputChange("phoneNumber", e.target.value)}
        />

        <Input
          label="Password"
          type="password"
          placeholder="Enter your password"
          value={formData.password}
          onChange={(e) => handleInputChange("password", e.target.value)}
          required
        />

        {mode === "register" && (
          <Input
            label="Confirm Password"
            type="password"
            placeholder="Confirm your password"
            value={formData.confirmPassword}
            onChange={(e) => handleInputChange("confirmPassword", e.target.value)}
            required
          />
        )}

        {error && (
          <div className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
            {error}
          </div>
        )}

        <Button
          type="submit"
          className="w-full"
          loading={isLoading}
          disabled={isLoading}
        >
          {mode === "login" ? "Sign In" : "Create Account"}
        </Button>
      </form>

      <div className="text-center text-sm">
        <button
          type="button"
          onClick={onToggleMode}
          className="text-primary hover:underline"
        >
          {mode === "login"
            ? "Don't have an account? Sign up"
            : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}