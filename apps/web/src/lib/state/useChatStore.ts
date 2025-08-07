"use client";

import { create } from "zustand";
import type { Message, Conversation, Language, Category } from "@ks-ai/types";

interface ChatState {
  currentConversation: Conversation | null;
  messages: Message[];
  isLoading: boolean;
  language: Language;
  topic: Category | null;
  
  setLanguage: (language: Language) => void;
  setTopic: (topic: Category) => void;
  setConversation: (conversation: Conversation) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  currentConversation: null,
  messages: [],
  isLoading: false,
  language: "en",
  topic: null,

  setLanguage: (language: Language) => {
    set({ language });
    if (typeof window !== "undefined") {
      sessionStorage.setItem("language", language);
    }
  },

  setTopic: (topic: Category) => {
    set({ topic });
    if (typeof window !== "undefined") {
      sessionStorage.setItem("topic", topic);
    }
  },

  setConversation: (conversation: Conversation) => {
    set({
      currentConversation: conversation,
      messages: conversation.messages || [],
    });
  },

  addMessage: (message: Message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  clearMessages: () => {
    set({ messages: [], currentConversation: null });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },
}));