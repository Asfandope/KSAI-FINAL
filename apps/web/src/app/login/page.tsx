"use client";

import React, { useState } from "react";
import { AuthForm } from "@/components/auth/AuthForm";

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");

  const toggleMode = () => {
    setMode(prev => prev === "login" ? "register" : "login");
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-8 bg-background">
      <AuthForm mode={mode} onToggleMode={toggleMode} />
    </main>
  );
}