"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/lib/state/useAuthStore";
import { Button, Input } from "@ks-ai/ui";
import { Upload, FileText, Youtube, Users, MessageCircle, Activity } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface DashboardStats {
  content_stats: {
    total: number;
    pending: number;
    processing: number;
    completed: number;
    failed: number;
  };
  total_users: number;
  total_conversations: number;
}

interface ContentItem {
  id: string;
  title: string;
  source_type: string;
  category: string;
  status: string;
  created_at: string;
}

export default function AdminPage() {
  const { user, token } = useAuthStore();
  const [activeTab, setActiveTab] = useState("dashboard");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    youtubeUrl: "",
    category: "Politics",
    language: "en",
    needsTranslation: false,
  });

  const loadDashboardData = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    }
  }, [token]);

  const loadContent = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/content`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setContent(data);
      }
    } catch (error) {
      console.error("Failed to load content:", error);
    }
  }, [token]);

  useEffect(() => {
    if (user?.role === "admin" && token) {
      loadDashboardData();
      loadContent();
    }
  }, [user, token, loadDashboardData, loadContent]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadForm.file && !uploadForm.youtubeUrl) {
      alert("Please provide either a file or YouTube URL");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      if (uploadForm.file) {
        formData.append("file", uploadForm.file);
      }
      if (uploadForm.youtubeUrl) {
        formData.append("youtube_url", uploadForm.youtubeUrl);
      }
      formData.append("category", uploadForm.category);
      formData.append("language", uploadForm.language);
      formData.append("needs_translation", String(uploadForm.needsTranslation));

      const response = await fetch(`${API_BASE}/admin/content`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (response.ok) {
        alert("Content uploaded successfully!");
        setUploadForm({
          file: null,
          youtubeUrl: "",
          category: "Politics",
          language: "en",
          needsTranslation: false,
        });
        loadContent();
        loadDashboardData();
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!user || user.role !== "admin") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-muted-foreground mb-4">You need admin privileges to access this page.</p>
          <Button onClick={() => window.location.href = "/login"}>
            Login as Admin
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">KS AI Admin Panel</h1>
          <p className="text-muted-foreground">Welcome, {user.email}</p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="flex space-x-1 mb-6">
          <Button
            variant={activeTab === "dashboard" ? "primary" : "outline"}
            onClick={() => setActiveTab("dashboard")}
          >
            <Activity className="w-4 h-4 mr-2" />
            Dashboard
          </Button>
          <Button
            variant={activeTab === "upload" ? "primary" : "outline"}
            onClick={() => setActiveTab("upload")}
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Content
          </Button>
          <Button
            variant={activeTab === "content" ? "primary" : "outline"}
            onClick={() => setActiveTab("content")}
          >
            <FileText className="w-4 h-4 mr-2" />
            Manage Content
          </Button>
        </div>

        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Dashboard</h2>
            
            {stats && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Total Users</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{stats.total_users}</p>
                </div>
                
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <MessageCircle className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Conversations</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{stats.total_conversations}</p>
                </div>
                
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Total Content</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{stats.content_stats.total}</p>
                </div>
              </div>
            )}

            {stats && (
              <div className="bg-card p-6 rounded-lg border">
                <h3 className="font-medium mb-4">Content Processing Status</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Completed</p>
                    <p className="text-xl font-bold text-green-600">{stats.content_stats.completed}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Processing</p>
                    <p className="text-xl font-bold text-blue-600">{stats.content_stats.processing}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Pending</p>
                    <p className="text-xl font-bold text-yellow-600">{stats.content_stats.pending}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Failed</p>
                    <p className="text-xl font-bold text-red-600">{stats.content_stats.failed}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "upload" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold">Upload New Content</h2>
            
            <form onSubmit={handleUpload} className="space-y-4 max-w-md">
              <div>
                <label className="block text-sm font-medium mb-2">Upload PDF File</label>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setUploadForm(prev => ({ 
                    ...prev, 
                    file: e.target.files?.[0] || null,
                    youtubeUrl: "" // Clear YouTube URL if file is selected
                  }))}
                  className="block w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                />
              </div>

              <div className="text-center text-sm text-muted-foreground">OR</div>

              <Input
                label="YouTube Video URL"
                value={uploadForm.youtubeUrl}
                onChange={(e) => setUploadForm(prev => ({ 
                  ...prev, 
                  youtubeUrl: e.target.value,
                  file: null // Clear file if YouTube URL is entered
                }))}
                placeholder="https://youtube.com/watch?v=..."
              />

              <div>
                <label className="block text-sm font-medium mb-2">Category</label>
                <select
                  value={uploadForm.category}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md"
                >
                  <option value="Politics">Politics</option>
                  <option value="Environmentalism">Environmentalism</option>
                  <option value="SKCRF">SKCRF</option>
                  <option value="Educational Trust">Educational Trust</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Language</label>
                <select
                  value={uploadForm.language}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, language: e.target.value }))}
                  className="w-full px-3 py-2 border border-border rounded-md"
                >
                  <option value="en">English</option>
                  <option value="ta">Tamil</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="needsTranslation"
                  checked={uploadForm.needsTranslation}
                  onChange={(e) => setUploadForm(prev => ({ ...prev, needsTranslation: e.target.checked }))}
                  className="rounded border-border"
                />
                <label htmlFor="needsTranslation" className="text-sm">
                  Needs AI Translation
                </label>
              </div>

              <Button
                type="submit"
                loading={loading}
                disabled={loading || (!uploadForm.file && !uploadForm.youtubeUrl)}
                className="w-full"
              >
                Upload Content
              </Button>
            </form>
          </div>
        )}

        {activeTab === "content" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Manage Content</h2>
              <Button onClick={loadContent} variant="outline" size="sm">
                Refresh
              </Button>
            </div>
            
            <div className="border rounded-lg">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="text-left p-4">Title</th>
                      <th className="text-left p-4">Type</th>
                      <th className="text-left p-4">Category</th>
                      <th className="text-left p-4">Status</th>
                      <th className="text-left p-4">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {content.map((item) => (
                      <tr key={item.id} className="border-b">
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            {item.source_type === "pdf" ? (
                              <FileText className="h-4 w-4 text-red-500" />
                            ) : (
                              <Youtube className="h-4 w-4 text-red-500" />
                            )}
                            <span className="font-medium">{item.title}</span>
                          </div>
                        </td>
                        <td className="p-4 text-sm text-muted-foreground">
                          {item.source_type.toUpperCase()}
                        </td>
                        <td className="p-4 text-sm">{item.category}</td>
                        <td className="p-4">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            item.status === "completed" ? "bg-green-100 text-green-800" :
                            item.status === "processing" ? "bg-blue-100 text-blue-800" :
                            item.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                            "bg-red-100 text-red-800"
                          }`}>
                            {item.status}
                          </span>
                        </td>
                        <td className="p-4 text-sm text-muted-foreground">
                          {new Date(item.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {content.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No content uploaded yet. Start by uploading some PDFs or YouTube videos.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}