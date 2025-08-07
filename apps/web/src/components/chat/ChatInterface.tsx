"use client";

import React, { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { useChatStore } from "@/lib/state/useChatStore";
import { useAuthStore } from "@/lib/state/useAuthStore";
import { Button } from "@ks-ai/ui";
import { MessageCircle, Loader2 } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function ChatInterface() {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { 
    messages, 
    isLoading, 
    language, 
    topic, 
    currentConversation,
    addMessage, 
    setLoading 
  } = useChatStore();
  const { token, user } = useAuthStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText: string) => {
    if (!token || !user || !topic) return;

    // Add user message immediately
    const userMessage = {
      id: `user-${Date.now()}`,
      conversationId: currentConversation?.id || "",
      sender: "user" as const,
      textContent: messageText,
      createdAt: new Date().toISOString(),
    };
    addMessage(userMessage);
    
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          query: messageText,
          language,
          topic,
          conversationId: currentConversation?.id,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const aiMessage = await response.json();
      addMessage(aiMessage);
    } catch (error) {
      console.error("Failed to send message:", error);
      // Add error message
      const errorMessage = {
        id: `error-${Date.now()}`,
        conversationId: currentConversation?.id || "",
        sender: "ai" as const,
        textContent: "Sorry, I couldn't process your message. Please try again.",
        createdAt: new Date().toISOString(),
      };
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <MessageCircle className="h-16 w-16 mx-auto text-muted-foreground" />
          <div>
            <h3 className="text-lg font-semibold">Please sign in</h3>
            <p className="text-muted-foreground">You need to be logged in to chat</p>
          </div>
          <Button onClick={() => window.location.href = "/login"}>
            Sign In
          </Button>
        </div>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center space-y-4">
          <MessageCircle className="h-16 w-16 mx-auto text-muted-foreground" />
          <div>
            <h3 className="text-lg font-semibold">Select a topic</h3>
            <p className="text-muted-foreground">Please go back and select a topic to start chatting</p>
          </div>
          <Button onClick={() => window.location.href = "/"}>
            Select Topic
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen max-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="space-y-1">
          <h1 className="text-lg font-semibold">KS AI Assistant</h1>
          <p className="text-sm text-muted-foreground">
            Topic: {topic} | Language: {language === "en" ? "English" : "தமிழ்"}
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => window.location.href = "/"}
        >
          Change Topic
        </Button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-4 max-w-md">
              <MessageCircle className="h-16 w-16 mx-auto text-muted-foreground" />
              <div>
                <h3 className="text-lg font-semibold">
                  Welcome to KS AI Assistant
                </h3>
                <p className="text-muted-foreground">
                  Ask me anything about {topic}. I'll provide credible, source-based answers.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center space-x-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}