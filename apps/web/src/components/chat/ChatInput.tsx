"use client";

import React, { useState } from "react";
import { Button, Input } from "@ks-ai/ui";
import { Send, Mic } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder = "Type your message..." }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleVoiceInput = () => {
    // TODO: Implement voice input functionality
    alert("Voice input will be implemented in the next phase");
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t bg-background">
      <div className="flex-1">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="border-0 bg-secondary/50 focus-visible:ring-1"
        />
      </div>
      
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleVoiceInput}
        disabled={disabled}
        className="shrink-0"
      >
        <Mic className="h-4 w-4" />
      </Button>
      
      <Button
        type="submit"
        size="sm"
        disabled={disabled || !message.trim()}
        className="shrink-0"
      >
        <Send className="h-4 w-4" />
      </Button>
    </form>
  );
}