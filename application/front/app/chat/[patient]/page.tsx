"use client";

import { useState, useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage({ params }: { params: { patient: string } }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const searchParams = useSearchParams();
  
  // Get client name from URL params if available, otherwise use patient param
  const clientNameFromUrl = searchParams.get('clientName');
  const patientName = clientNameFromUrl || params.patient.replace("-", " ");
  const capitalizedName = patientName.split(" ").map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(" ");

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize chat when component mounts
    const initChat = async () => {
      try {
        const response = await fetch("http://localhost:8000/chat/start", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ client_name: capitalizedName }),
        });

        if (response.ok) {
          const data = await response.json();
          setMessages(data.messages || []);
        }
      } catch (error) {
        console.error("Error initializing chat:", error);
      } finally {
        setLoading(false);
      }
    };

    initChat();
  }, [capitalizedName]);

  const sendMessage = async () => {
    if (!input.trim() || sending) return;

    const userMessage: ChatMessage = { role: "user", content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    setSending(true);

    try {
      const response = await fetch("http://localhost:8000/chat/send", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (response.ok) {
        const assistantMessage = await response.json();
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#181028] via-[#1a1333] to-black flex items-center justify-center">
        <div className="bg-[#1a1333]/80 p-10 rounded-3xl shadow-2xl flex flex-col items-center border border-[#A259F7]/30">
          <div className="animate-spin rounded-full h-14 w-14 border-b-4 border-[#A259F7] mb-6"></div>
          <p className="text-white font-semibold text-lg">Initializing chat with MedGemma...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#181028] via-[#1a1333] to-black flex flex-col">
      {/* Header */}
      <div className="bg-[#1a1333]/80 shadow-sm border-b border-[#A259F7]/20">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-extrabold text-white tracking-tight drop-shadow-lg">Chat with <span className='text-[#A259F7]'>MedGemma</span></h1>
              <p className="text-[#E0D7F7]">Patient: {capitalizedName}</p>
            </div>
            <Link 
              href="/"
              className="px-5 py-2 bg-gradient-to-r from-[#3B1E6D] to-[#A259F7] text-white rounded-2xl hover:from-[#A259F7] hover:to-[#3B1E6D] transition-colors shadow-lg border border-[#A259F7]/40 font-semibold text-lg"
              style={{ boxShadow: '0 0 8px #A259F7aa' }}
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 container mx-auto px-6 py-6 overflow-hidden">
        <div className="bg-[#1a1333]/80 rounded-3xl shadow-2xl h-full flex flex-col border border-[#A259F7]/30 backdrop-blur-md">
          <div className="flex-1 p-8 overflow-y-auto space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-6 py-4 rounded-2xl shadow-md border font-medium text-base ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-[#A259F7] to-[#3B1E6D] text-white border-[#A259F7]/40"
                      : "bg-[#221a36] text-[#E0D7F7] border-[#A259F7]/10"
                  }`}
                  style={message.role === "user" ? { boxShadow: '0 0 8px #A259F7aa' } : {}}
                >
                  {message.role === "assistant" ? (
                    <div className="text-base leading-relaxed">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-base leading-relaxed">{message.content}</p>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-[#221a36] text-[#E0D7F7] max-w-xs lg:max-w-md px-6 py-4 rounded-2xl shadow-md border border-[#A259F7]/10">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-[#A259F7] rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-[#A259F7] rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                      <div className="w-2 h-2 bg-[#A259F7] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-[#A259F7]/20 p-6 bg-[#221a36]/60 rounded-b-3xl">
            <div className="flex space-x-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="flex-1 px-5 py-4 border border-[#A259F7]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#A259F7] focus:border-transparent bg-[#181028] text-white placeholder-[#A259F7]/60 font-medium text-base"
                disabled={sending}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || sending}
                className="px-6 py-4 bg-gradient-to-r from-[#A259F7] to-[#3B1E6D] text-white rounded-xl hover:from-[#3B1E6D] hover:to-[#A259F7] transition-colors font-semibold shadow-lg border border-[#A259F7]/40 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                style={{ boxShadow: '0 0 8px #A259F7aa' }}
              >
                <svg 
                  className="w-5 h-5" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
