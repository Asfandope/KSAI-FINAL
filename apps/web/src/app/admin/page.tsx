"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/lib/state/useAuthStore";
import { Button, Input } from "@ks-ai/ui";
import { Upload, FileText, Youtube, Users, MessageCircle, Activity, Database, Settings, Search, X } from "lucide-react";

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

  // Knowledge Base state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchCategory, setSearchCategory] = useState("all");
  const [searchResults, setSearchResults] = useState([]);
  const [knowledgeBaseStats, setKnowledgeBaseStats] = useState(null);
  const [testQuery, setTestQuery] = useState("");
  const [testTopic, setTestTopic] = useState("general");
  const [testResponse, setTestResponse] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [reindexLoading, setReindexLoading] = useState(false);

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

  // Knowledge Base functions
  const loadKnowledgeBaseStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/admin/knowledge-base/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setKnowledgeBaseStats(data);
      }
    } catch (error) {
      console.error("Failed to load knowledge base stats:", error);
    }
  }, [token]);

  const searchKnowledgeBase = async () => {
    if (!searchQuery.trim()) return;
    
    setSearchLoading(true);
    try {
      const params = new URLSearchParams({ 
        query: searchQuery,
        limit: "20"
      });
      
      if (searchCategory !== "all") {
        params.append("category", searchCategory);
      }
      
      const response = await fetch(`${API_BASE}/admin/knowledge-base/search?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.results || []);
      } else {
        console.error("Search failed:", response.status);
        alert("Search failed. Please try again.");
      }
    } catch (error) {
      console.error("Knowledge base search failed:", error);
      alert("Search failed. Please try again.");
    } finally {
      setSearchLoading(false);
    }
  };

  const testKnowledgeBase = async () => {
    if (!testQuery.trim()) return;
    
    setTestLoading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/knowledge-base/test-query`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query: testQuery,
          topic: testTopic,
          language: "en"
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log("RAG Response:", data); // Debug log
        setTestResponse(data);
      } else {
        const errorText = await response.text();
        console.error("Test query failed:", response.status, errorText);
        alert("Test query failed. Please try again.");
      }
    } catch (error) {
      console.error("RAG test failed:", error);
      alert("RAG test failed. Please try again.");
    } finally {
      setTestLoading(false);
    }
  };

  const reindexCategory = async (category) => {
    setReindexLoading(true);
    try {
      const response = await fetch(`${API_BASE}/admin/knowledge-base/reindex/${category}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        alert(`Reindexing started for ${category}`);
        loadKnowledgeBaseStats();
      } else {
        alert("Reindexing failed. Please try again.");
      }
    } catch (error) {
      console.error("Reindexing failed:", error);
      alert("Reindexing failed. Please try again.");
    } finally {
      setReindexLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin" && token) {
      loadDashboardData();
      loadContent();
      if (activeTab === "knowledge-base") {
        loadKnowledgeBaseStats();
      }
    }
  }, [user, token, activeTab, loadDashboardData, loadContent, loadKnowledgeBaseStats]);

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
          <Button
            variant={activeTab === "knowledge-base" ? "primary" : "outline"}
            onClick={() => setActiveTab("knowledge-base")}
          >
            <Search className="w-4 h-4 mr-2" />
            Knowledge Base
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

        {activeTab === "knowledge-base" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Knowledge Base Management</h2>
              <Button onClick={loadKnowledgeBaseStats} variant="outline" size="sm">
                Refresh Stats
              </Button>
            </div>

            {/* Statistics Dashboard */}
            {knowledgeBaseStats && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <Database className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Total Documents</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{knowledgeBaseStats.total_documents}</p>
                </div>
                
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <Search className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Total Vectors</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{knowledgeBaseStats.total_vectors}</p>
                </div>
                
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <Users className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Active Sessions</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{knowledgeBaseStats.general?.active_sessions || 0}</p>
                </div>
                
                <div className="bg-card p-6 rounded-lg border">
                  <div className="flex items-center space-x-2">
                    <Settings className="h-5 w-5 text-primary" />
                    <h3 className="font-medium">Languages</h3>
                  </div>
                  <p className="text-2xl font-bold mt-2">{knowledgeBaseStats.general?.languages_supported?.length || 2}</p>
                </div>
              </div>
            )}

            {/* Search & Test Interface */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Search Section */}
              <div className="bg-card p-6 rounded-lg border">
                <h3 className="font-medium mb-4">Search Knowledge Base</h3>
                <div className="space-y-4">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Enter search query..."
                    onKeyPress={(e) => e.key === 'Enter' && searchKnowledgeBase()}
                  />
                  
                  <div className="flex space-x-2">
                    <select
                      value={searchCategory}
                      onChange={(e) => setSearchCategory(e.target.value)}
                      className="px-3 py-2 border border-border rounded-md"
                    >
                      <option value="all">All Categories</option>
                      <option value="Politics">Politics</option>
                      <option value="Environmentalism">Environmentalism</option>
                      <option value="SKCRF">SKCRF</option>
                      <option value="Educational Trust">Educational Trust</option>
                    </select>
                    
                    <Button
                      onClick={searchKnowledgeBase}
                      loading={searchLoading}
                      disabled={!searchQuery.trim()}
                    >
                      <Search className="w-4 h-4 mr-2" />
                      Search
                    </Button>
                  </div>

                  {searchResults.length > 0 && (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {searchResults.map((result, index) => (
                        <div key={index} className="p-3 border rounded-md">
                          <div className="flex justify-between items-start mb-2">
                            <span className="text-sm font-medium">{result.category}</span>
                            <span className="text-xs text-muted-foreground">
                              Score: {(result.score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-sm">{result.content?.substring(0, 200)}...</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* RAG Test Section */}
              <div className="bg-card p-6 rounded-lg border">
                <h3 className="font-medium mb-4">Test RAG Query</h3>
                <div className="space-y-4">
                  <Input
                    value={testQuery}
                    onChange={(e) => setTestQuery(e.target.value)}
                    placeholder="Enter test question..."
                  />
                  
                  <div className="flex space-x-2">
                    <select
                      value={testTopic}
                      onChange={(e) => setTestTopic(e.target.value)}
                      className="px-3 py-2 border border-border rounded-md"
                    >
                      <option value="general">General</option>
                      <option value="Politics">Politics</option>
                      <option value="Environmentalism">Environmentalism</option>
                      <option value="SKCRF">SKCRF</option>
                      <option value="Educational Trust">Educational Trust</option>
                    </select>
                    
                    <Button
                      onClick={testKnowledgeBase}
                      loading={testLoading}
                      disabled={!testQuery.trim()}
                    >
                      Test Query
                    </Button>
                  </div>

                  {testResponse && (
                    <div className="space-y-3">
                      <div className="p-3 bg-muted rounded-md">
                        <h4 className="font-medium text-sm mb-2">Response:</h4>
                        <p className="text-sm">{testResponse.response || testResponse.answer || "No response received"}</p>
                      </div>
                      
                      {testResponse.sources && testResponse.sources.length > 0 && (
                        <div className="p-3 border rounded-md">
                          <h4 className="font-medium text-sm mb-2">Sources:</h4>
                          <div className="space-y-1">
                            {testResponse.sources.map((source, index) => (
                              <div key={index} className="text-xs text-muted-foreground">
                                {source.title || source.content?.substring(0, 50) || `Source ${index + 1}`} 
                                {source.score && !isNaN(source.score) && (
                                  <span> (Score: {(source.score * 100).toFixed(1)}%)</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {testResponse.context && testResponse.context.length > 0 && (
                        <div className="p-3 border rounded-md">
                          <h4 className="font-medium text-sm mb-2">Context Used:</h4>
                          <div className="space-y-1">
                            {testResponse.context.map((ctx, index) => (
                              <div key={index} className="text-xs text-muted-foreground">
                                {ctx.content?.substring(0, 100)}...
                                {ctx.metadata?.score && !isNaN(ctx.metadata.score) && (
                                  <span> (Score: {(ctx.metadata.score * 100).toFixed(1)}%)</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Category Management */}
            {knowledgeBaseStats?.categories && (
              <div className="bg-card p-6 rounded-lg border">
                <h3 className="font-medium mb-4">Category Management</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(knowledgeBaseStats.categories).map(([category, stats]) => (
                    <div key={category} className="p-4 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium text-sm">{category}</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => reindexCategory(category)}
                          disabled={reindexLoading}
                        >
                          Reindex
                        </Button>
                      </div>
                      <div className="space-y-1">
                        <div className="text-xs text-muted-foreground">
                          Documents: {stats.documents}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Vectors: {stats.vectors}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}