"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { ROLE_LABELS, formatDateTime } from "@/lib/utils";
import {
  MessageSquare, Send, Plus, FileText, ChevronRight, Loader2,
  Lightbulb, HardHat,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface Citation {
  document_id: string;
  file_name: string;
  page_number: number | null;
  snippet: string;
  relevance_score: number;
}

interface Message {
  id: string;
  role: string;
  content: string;
  citations: Citation[];
  created_at: string;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  last_message: string | null;
}

const SUGGESTIONS = [
  "What changed in the latest revision?",
  "Which submittal is approved for curtain wall anchors?",
  "What was recorded in the daily report for this week?",
  "Summarize the electrical specifications.",
  "Are there any open RFIs for the foundation work?",
  "What safety requirements apply to elevated work?",
];

export default function ChatPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [showSources, setShowSources] = useState<Citation[] | null>(null);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get<any>(`/projects/${projectId}`),
  });

  const { data: sessions = [], refetch: refetchSessions } = useQuery({
    queryKey: ["chatSessions", projectId],
    queryFn: () => api.get<Session[]>(`/projects/${projectId}/chat/sessions`),
  });

  const { data: messages = [], refetch: refetchMessages } = useQuery({
    queryKey: ["chatMessages", projectId, activeSession],
    queryFn: () =>
      activeSession
        ? api.get<Message[]>(`/projects/${projectId}/chat/sessions/${activeSession}`)
        : Promise.resolve([]),
    enabled: !!activeSession,
  });

  const createSession = useMutation({
    mutationFn: () => api.post<Session>(`/projects/${projectId}/chat/sessions`, { title: "New Chat" }),
    onSuccess: (session) => {
      setActiveSession(session.id);
      refetchSessions();
    },
  });

  const sendMessage = useMutation({
    mutationFn: (content: string) =>
      api.post<any>(`/projects/${projectId}/chat/sessions/${activeSession}/messages`, { content }),
    onSuccess: () => {
      refetchMessages();
      refetchSessions();
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || sendMessage.isPending) return;
    if (!activeSession) {
      const session = await createSession.mutateAsync();
      setActiveSession(session.id);
      // Need to wait a tick then send
      setTimeout(async () => {
        const msg = input.trim();
        setInput("");
        await api.post(`/projects/${projectId}/chat/sessions/${session.id}/messages`, { content: msg });
        refetchMessages();
        refetchSessions();
      }, 100);
      return;
    }
    const msg = input.trim();
    setInput("");
    sendMessage.mutate(msg);
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
  };

  return (
    <div className="flex h-[calc(100vh)] overflow-hidden">
      {/* Session sidebar */}
      <div className="w-72 border-r border-surface-border bg-surface-paper flex flex-col">
        <div className="p-4 border-b border-surface-border">
          <button onClick={() => createSession.mutate()} className="btn-primary w-full flex items-center justify-center gap-2 py-2">
            <Plus className="w-4 h-4" /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={`w-full text-left p-3 border-b border-surface-border hover:bg-surface-muted transition-colors ${
                activeSession === s.id ? "bg-surface-muted" : ""
              }`}
            >
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-hard-concrete flex-shrink-0" />
                <p className="text-sm font-medium text-hard-beam truncate">{s.title}</p>
              </div>
              {s.last_message && (
                <p className="text-xs text-hard-concrete mt-1 truncate pl-6">{s.last_message}</p>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="px-6 py-3 border-b border-surface-border bg-surface-paper flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-hard-hat/10 rounded-lg flex items-center justify-center">
              <HardHat className="w-4 h-4 text-hard-hat" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-hard-beam">{project?.name || "Project"} Chat</h2>
              <p className="text-xs text-hard-concrete">
                {project?.my_role && ROLE_LABELS[project.my_role]}
              </p>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!activeSession && messages.length === 0 && (
            <div className="max-w-2xl mx-auto text-center py-16">
              <div className="w-16 h-16 bg-hard-hat/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <MessageSquare className="w-8 h-8 text-hard-hat" />
              </div>
              <h2 className="text-xl font-bold text-hard-beam mb-2">Ask your project documents</h2>
              <p className="text-hard-concrete mb-8">
                Every answer is grounded in your project documents with citations.
                Only documents you have access to are used.
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-lg mx-auto">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSuggestion(s)}
                    className="text-left p-3 card hover:shadow-md transition-shadow text-sm text-hard-slate"
                  >
                    <Lightbulb className="w-4 h-4 text-hard-hat mb-1" />
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
              {msg.role === "assistant" && (
                <div className="w-8 h-8 bg-hard-hat/10 rounded-lg flex items-center justify-center flex-shrink-0 mt-1">
                  <HardHat className="w-4 h-4 text-hard-hat" />
                </div>
              )}
              <div className={`max-w-[70%] ${msg.role === "user" ? "bg-hard-steel text-white rounded-2xl rounded-tr-sm px-4 py-3" : ""}`}>
                {msg.role === "assistant" ? (
                  <div className="space-y-3">
                    <div className="prose prose-sm max-w-none text-hard-beam whitespace-pre-wrap">
                      {msg.content}
                    </div>
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {msg.citations.map((c: Citation, i: number) => (
                          <Link
                            key={i}
                            href={`/projects/${projectId}/documents/${c.document_id}?page=${c.page_number || 1}`}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-surface-muted rounded-lg text-xs hover:bg-hard-hat/10 hover:text-hard-hat transition-colors group"
                          >
                            <FileText className="w-3 h-3 text-hard-concrete group-hover:text-hard-hat" />
                            <span className="font-medium truncate max-w-[150px]">{c.file_name}</span>
                            {c.page_number && <span className="text-hard-concrete">p.{c.page_number}</span>}
                          </Link>
                        ))}
                        <button
                          onClick={() => setShowSources(msg.citations)}
                          className="text-xs text-hard-steel hover:underline"
                        >
                          View all sources
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm">{msg.content}</p>
                )}
              </div>
            </div>
          ))}

          {sendMessage.isPending && (
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-hard-hat/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Loader2 className="w-4 h-4 text-hard-hat animate-spin" />
              </div>
              <div className="bg-surface-muted rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2 text-sm text-hard-concrete">
                  <span>Searching documents and generating answer...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-surface-border bg-surface-paper">
          <div className="max-w-4xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
              placeholder="Ask about your project documents..."
              className="input-field flex-1"
              disabled={sendMessage.isPending}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || sendMessage.isPending}
              className="btn-primary px-4"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Sources drawer */}
      {showSources && (
        <div className="w-80 border-l border-surface-border bg-surface-paper overflow-y-auto">
          <div className="p-4 border-b border-surface-border flex items-center justify-between">
            <h3 className="font-semibold text-hard-beam">Sources</h3>
            <button onClick={() => setShowSources(null)} className="text-hard-concrete hover:text-hard-beam">
              &times;
            </button>
          </div>
          <div className="p-4 space-y-3">
            {showSources.map((c, i) => (
              <Link
                key={i}
                href={`/projects/${projectId}/documents/${c.document_id}?page=${c.page_number || 1}`}
                className="block card p-3 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-hard-hat" />
                  <span className="text-sm font-medium text-hard-beam truncate">{c.file_name}</span>
                </div>
                {c.page_number && (
                  <span className="badge bg-surface-muted text-hard-concrete mb-2">Page {c.page_number}</span>
                )}
                <p className="text-xs text-hard-concrete line-clamp-4">{c.snippet}</p>
                <div className="mt-2 text-xs text-hard-steel">
                  Relevance: {(c.relevance_score * 100).toFixed(0)}%
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
