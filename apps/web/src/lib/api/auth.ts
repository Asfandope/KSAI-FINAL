"use client";

import type { User, RegisterRequest, LoginRequest, TokenResponse } from "@ks-ai/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class AuthAPI {
  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "An error occurred" }));
      throw new Error(error.detail || "Request failed");
    }
    
    return response.json();
  }

  async register(data: RegisterRequest): Promise<User> {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async login(data: LoginRequest): Promise<TokenResponse> {
    return this.request("/auth/login", {
      method: "POST", 
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser(token: string): Promise<User> {
    return this.request("/auth/me", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  async getTopics(): Promise<string[]> {
    return this.request("/topics");
  }
}

export const authAPI = new AuthAPI();