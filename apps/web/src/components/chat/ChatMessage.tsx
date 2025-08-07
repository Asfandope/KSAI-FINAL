"use client";

import React from "react";
import type { Message } from "@ks-ai/types";
import { cn } from "@ks-ai/ui";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.sender === "user";
  
  return (
    <div className={cn(
      "flex w-full mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "max-w-[80%] rounded-lg px-4 py-2",
        isUser
          ? "bg-primary text-primary-foreground ml-auto"
          : "bg-secondary text-secondary-foreground mr-auto"
      )}>
        <div className="text-sm whitespace-pre-wrap">
          {message.textContent}
        </div>
        
        {message.imageUrl && (
          <div className="mt-2">
            <img 
              src={message.imageUrl} 
              alt="Shared image"
              className="max-w-full h-auto rounded-md"
            />
          </div>
        )}
        
        {message.videoUrl && (
          <div className="mt-2">
            <iframe
              src={`${message.videoUrl}${message.videoTimestamp ? `?t=${message.videoTimestamp}` : ''}`}
              className="w-full h-48 rounded-md"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        )}
        
        <div className={cn(
          "text-xs mt-1 opacity-70",
          isUser ? "text-right" : "text-left"
        )}>
          {new Date(message.createdAt).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}