"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useChatStore } from "@/lib/state/useChatStore";
import { useAuthStore } from "@/lib/state/useAuthStore";
import type { Language, Category } from "@ks-ai/types";
import { Settings } from "lucide-react";

const topics: Record<Language, { en: Category; display: string }[]> = {
  en: [
    { en: "Politics", display: "Politics" },
    { en: "Environmentalism", display: "Environmentalism" },
    { en: "SKCRF", display: "SKCRF" },
    { en: "Educational Trust", display: "Educational Trust" }
  ],
  ta: [
    { en: "Politics", display: "அரசியல்" },
    { en: "Environmentalism", display: "சுற்றுச்சூழல்" },
    { en: "SKCRF", display: "SKCRF" },
    { en: "Educational Trust", display: "கல்வி அறக்கட்டளை" }
  ],
};

export default function Home() {
  const router = useRouter();
  const { setLanguage, setTopic, clearMessages } = useChatStore();
  const { user } = useAuthStore();
  const [selectedLanguage, setSelectedLanguage] = useState<Language | null>(null);

  useEffect(() => {
    // Clear any existing chat data when returning to home
    clearMessages();
  }, [clearMessages]);

  const handleLanguageSelect = (lang: Language) => {
    setSelectedLanguage(lang);
    setLanguage(lang);
  };

  const handleTopicSelect = (topicData: { en: Category; display: string }) => {
    if (selectedLanguage) {
      setTopic(topicData.en);
      router.push("/chat");
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="w-full max-w-4xl space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary">KS AI Assistant</h1>
          <p className="text-lg text-muted-foreground">
            Get credible answers about Karthikeya Sivasenapathy's work
          </p>
        </div>

        {!selectedLanguage ? (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-center">
              Choose Your Language / உங்கள் மொழியைத் தேர்ந்தெடுக்கவும்
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => handleLanguageSelect("en")}
                className="p-8 border-2 border-border rounded-lg hover:border-primary hover:bg-secondary transition-all"
              >
                <div className="text-2xl font-bold mb-2">English</div>
                <div className="text-muted-foreground">
                  Continue in English
                </div>
              </button>
              <button
                onClick={() => handleLanguageSelect("ta")}
                className="p-8 border-2 border-border rounded-lg hover:border-primary hover:bg-secondary transition-all"
              >
                <div className="text-2xl font-bold mb-2">தமிழ்</div>
                <div className="text-muted-foreground">
                  தமிழில் தொடரவும்
                </div>
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold">
                {selectedLanguage === "en" ? "Select a Topic" : "ஒரு தலைப்பைத் தேர்ந்தெடுக்கவும்"}
              </h2>
              <button
                onClick={() => setSelectedLanguage(null)}
                className="text-primary hover:underline"
              >
                {selectedLanguage === "en" ? "Change Language" : "மொழியை மாற்று"}
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {topics[selectedLanguage].map((topicData, index) => (
                <button
                  key={index}
                  onClick={() => handleTopicSelect(topicData)}
                  className="p-6 border-2 border-border rounded-lg hover:border-primary hover:bg-secondary transition-all text-left"
                >
                  <div className="text-xl font-semibold mb-2">{topicData.display}</div>
                  <div className="text-sm text-muted-foreground">
                    {selectedLanguage === "en" 
                      ? `Learn about KS's work in ${topicData.en}`
                      : `KS இன் பணி பற்றி அறிக`}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="text-center space-y-4 pt-8">
          <div className="text-sm text-muted-foreground">
            {user ? (
              <div className="flex items-center justify-center space-x-4">
                <span>Welcome, {user.email || user.phone_number}!</span>
                <button
                  onClick={() => {
                    // Logout functionality
                    const { logout } = useAuthStore.getState();
                    logout();
                  }}
                  className="text-primary hover:underline"
                >
                  Sign out
                </button>
                {(user.email === "admin@ksai.com" || user.role === "admin") && (
                  <button
                    onClick={() => router.push("/admin")}
                    className="inline-flex items-center space-x-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Admin Panel</span>
                  </button>
                )}
              </div>
            ) : (
              <div>
                <a href="/login" className="text-primary hover:underline">
                  Sign in to save your conversations
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}