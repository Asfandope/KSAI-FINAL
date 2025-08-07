"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@ks-ai/ui";
import { Volume2, VolumeX } from "lucide-react";
import type { Message } from "@ks-ai/types";
import { cn } from "@ks-ai/ui";

interface ChatMessageProps {
  message: Message;
  language?: string; // 'en' or 'ta' for language-specific TTS
}

export function ChatMessage({ message, language = "en" }: ChatMessageProps) {
  const isUser = message.sender === "user";
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);

  // Check for browser support
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);
    }
  }, []);

  // Clean up speech synthesis when component unmounts
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const handleSpeak = () => {
    if (!isSupported || !window.speechSynthesis) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }

    if (isSpeaking) {
      // Stop current speech
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(message.textContent);
    
    // Set language based on the conversation language
    utterance.lang = language === "ta" ? "ta-IN" : "en-US";
    
    // Configure speech settings
    utterance.rate = 0.9; // Slightly slower for better comprehension
    utterance.pitch = 1.0;
    utterance.volume = 0.8;

    // Try to find an appropriate voice
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      const preferredVoice = voices.find(voice => 
        voice.lang.startsWith(language === "ta" ? "ta" : "en")
      ) || voices.find(voice => voice.default) || voices[0];
      
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }
    }

    // Set up event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event.error);
      setIsSpeaking(false);
      
      let errorMessage = 'Text-to-speech failed. ';
      switch (event.error) {
        case 'not-allowed':
          errorMessage += 'Speech synthesis permission was denied.';
          break;
        case 'network':
          errorMessage += 'Network error occurred.';
          break;
        case 'synthesis-failed':
          errorMessage += 'Speech synthesis failed.';
          break;
        default:
          errorMessage += 'Please try again.';
      }
      
      alert(errorMessage);
    };

    // Start speaking
    window.speechSynthesis.speak(utterance);
  };

  const speakButtonTitle = isSpeaking 
    ? "Stop reading message" 
    : "Read message aloud";
  
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
          "flex items-center justify-between mt-1",
          isUser ? "flex-row-reverse" : "flex-row"
        )}>
          <div className={cn(
            "text-xs opacity-70",
            isUser ? "text-right" : "text-left"
          )}>
            {(() => {
              try {
                // Debug logging
                console.log('Timestamp debug:', { 
                  createdAt: message.createdAt, 
                  type: typeof message.createdAt 
                });
                
                const date = new Date(message.createdAt);
                if (isNaN(date.getTime())) {
                  console.warn('Invalid date, using current time:', message.createdAt);
                  return new Date().toLocaleTimeString();
                }
                return date.toLocaleTimeString();
              } catch (error) {
                console.error('Date parsing error:', error, message.createdAt);
                return new Date().toLocaleTimeString();
              }
            })()}
          </div>
          
          {/* Speaker button - only show for AI messages */}
          {!isUser && isSupported && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSpeak}
              disabled={!isSupported}
              className={cn(
                "h-6 w-6 p-0 ml-2 opacity-70 hover:opacity-100",
                isSpeaking ? "text-blue-600" : "text-muted-foreground"
              )}
              title={speakButtonTitle}
            >
              {isSpeaking ? (
                <VolumeX className="h-3 w-3" />
              ) : (
                <Volume2 className="h-3 w-3" />
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}