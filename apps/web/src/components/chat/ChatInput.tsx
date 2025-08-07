"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button, Input } from "@ks-ai/ui";
import { Send, Mic, MicOff } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder = "Type your message..." }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check for browser support and initialize speech recognition
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      if (SpeechRecognition) {
        setIsSupported(true);
        
        try {
          recognitionRef.current = new SpeechRecognition();
          
          const recognition = recognitionRef.current;
          recognition.continuous = false;
          recognition.interimResults = true;
          recognition.lang = 'en-US';
          recognition.maxAlternatives = 1;

          recognition.onstart = () => {
            console.log('Speech recognition started');
            setIsListening(true);
          };

          recognition.onresult = (event) => {
            console.log('Speech recognition result:', event);
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
              if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
              }
            }
            
            if (transcript.trim()) {
              setMessage(transcript.trim());
            }
          };

          recognition.onend = () => {
            console.log('Speech recognition ended');
            setIsListening(false);
          };

          recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error, event);
            setIsListening(false);
            
            // Show user-friendly error messages
            let errorMessage = 'Voice input failed. ';
            switch (event.error) {
              case 'no-speech':
                errorMessage += 'No speech was detected. Please try again.';
                break;
              case 'audio-capture':
                errorMessage += 'No microphone was found. Please check your microphone settings.';
                break;
              case 'not-allowed':
                errorMessage += 'Microphone permission was denied. Please enable microphone access.';
                break;
              case 'network':
                errorMessage += 'Network error occurred. Please check your connection.';
                break;
              case 'service-not-allowed':
                errorMessage += 'Speech service is not allowed. Please check your browser settings.';
                break;
              default:
                errorMessage += `Error: ${event.error}. Please try again.`;
            }
            
            console.warn(errorMessage);
            alert(errorMessage);
          };
        } catch (error) {
          console.error('Failed to initialize speech recognition:', error);
          setIsSupported(false);
        }
      } else {
        console.log('Speech recognition not supported in this browser');
        setIsSupported(false);
      }
    }
    
    setIsInitializing(false);

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (error) {
          console.warn('Error aborting speech recognition:', error);
        }
      }
    };
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleVoiceInput = async () => {
    console.log('handleVoiceInput called', { isSupported, isListening, hasRecognition: !!recognitionRef.current });
    
    if (!isSupported) {
      const message = "Voice input is not supported in this browser. Please use Chrome, Safari, or Edge.";
      console.warn(message);
      alert(message);
      return;
    }

    if (!recognitionRef.current) {
      const message = "Voice recognition is not available.";
      console.error(message);
      alert(message);
      return;
    }

    if (isListening) {
      // Stop listening
      console.log('Stopping speech recognition...');
      try {
        recognitionRef.current.stop();
      } catch (error) {
        console.error('Error stopping speech recognition:', error);
        setIsListening(false);
      }
      return;
    }

    try {
      console.log('Requesting microphone permission...');
      // Request microphone permission first
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Stop the stream immediately as we just needed permission
      stream.getTracks().forEach(track => track.stop());
      
      console.log('Starting speech recognition...');
      recognitionRef.current.start();
    } catch (error) {
      console.error('Microphone access error:', error);
      const message = "Microphone access was denied. Please enable microphone permissions and try again.";
      alert(message);
    }
  };

  const voiceButtonTitle = isInitializing
    ? "Initializing voice input..."
    : isListening 
      ? "Stop voice input" 
      : isSupported 
        ? "Start voice input" 
        : "Voice input not supported";

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 p-4 border-t bg-background">
      <div className="flex-1">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={isListening ? "Listening..." : placeholder}
          disabled={disabled}
          className="border-0 bg-secondary/50 focus-visible:ring-1"
        />
      </div>
      
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={handleVoiceInput}
        disabled={disabled || isInitializing || !isSupported}
        className={`shrink-0 transition-colors ${
          isInitializing
            ? 'opacity-50 cursor-wait'
            : isListening 
              ? 'bg-red-100 border-red-300 text-red-600 hover:bg-red-200' 
              : isSupported 
                ? 'hover:bg-blue-50 hover:border-blue-300' 
                : 'opacity-50 cursor-not-allowed'
        }`}
        title={voiceButtonTitle}
      >
        {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
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