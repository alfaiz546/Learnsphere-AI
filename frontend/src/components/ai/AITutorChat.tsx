import React, { useState, useRef, useEffect, useCallback } from 'react';
import { AIConversation, AIMessage } from '../../types';
import {
  aiService,
  generateIdempotencyKey,
  consumeIdempotencyKey,
} from '../../services/ai';
import { ChatMessage } from './ChatMessage';
import { ConversationSidebar } from './ConversationSidebar';
import { Button } from '../ui/Button';
import {
  Bot,
  Send,
  Sparkles,
  RefreshCcw,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';

interface AITutorChatProps {
  context?: {
    subject?: string;
    course?: string;
    lesson?: string;
    question?: string;
    student_answer?: string;
  };
  initialPrompt?: string;
  compact?: boolean;
}

export const AITutorChat: React.FC<AITutorChatProps> = ({
  context,
  initialPrompt,
  compact = false,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(!compact);
  const [activeConversation, setActiveConversation] = useState<AIConversation | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([
    {
      role: 'assistant',
      content:
        initialPrompt ||
        "Hello! I'm your LearnSphere AI Mentor. Ask me any question, request a hint, or let's break down tricky concepts together!",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [lastError, setLastError] = useState<string | null>(null);
  const [lastTurnId, setLastTurnId] = useState<string | undefined>();
  const [pendingIdempotencyKey, setPendingIdempotencyKey] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  // Load historical messages when conversation is selected
  const loadHistory = useCallback(async (conv: AIConversation) => {
    setHistoryLoading(true);
    setLastError(null);
    setLastTurnId(undefined);
    try {
      const res = await aiService.getConversationHistory(conv.id, 50, 0);
      if (res.success) {
        const historyMsgs: AIMessage[] = res.data.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          sequence_number: m.sequence_number,
          turn_id: m.turn_id,
          created_at: m.created_at,
        }));
        setMessages(
          historyMsgs.length > 0
            ? historyMsgs
            : [
                {
                  role: 'assistant',
                  content: 'Session loaded. What would you like to explore?',
                },
              ]
        );
      }
    } catch {
      setMessages([
        {
          role: 'assistant',
          content: 'Could not load conversation history. You can continue chatting.',
        },
      ]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const handleSelectConversation = useCallback(
    (conv: AIConversation) => {
      setActiveConversation(conv);
      loadHistory(conv);
    },
    [loadHistory]
  );

  const handleNewConversation = useCallback(() => {
    setActiveConversation(null);
    setLastTurnId(undefined);
    setPendingIdempotencyKey(null);
    setLastError(null);
    setMessages([
      {
        role: 'assistant',
        content:
          "Starting fresh! I'm ready for your questions.",
      },
    ]);
  }, []);

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || loading) return;

    // Generate a stable idempotency key for this logical submission.
    // Reuse the existing key for retries; generate a new one for new messages.
    let idempotencyKey = pendingIdempotencyKey;
    if (!idempotencyKey) {
      const newKey = generateIdempotencyKey();
      setPendingIdempotencyKey(newKey);
      idempotencyKey = newKey;
    }
    // Use the resolved idempotencyKey for the request
    // (instead of reading stale state directly)

    const userMsg: AIMessage = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setLastError(null);

    try {
      const res = await aiService.chat(
        textToSend,
        context,
        activeConversation?.id,
        idempotencyKey,
      );

      if (res.data) {
        const data = res.data;

        // Update active conversation if new one was created
        if (!activeConversation && data.conversation_id) {
          // Create a minimal conversation object; sidebar will refresh on its own
          setActiveConversation({
            id: data.conversation_id,
            student_id: '',
            title: textToSend.slice(0, 50),
            context_type: 'general',
            last_sequence_number: data.sequence_number ?? 1,
            last_turn_number: 1,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
        }

        setLastTurnId(data.turn_id);

        const assistantMsg: AIMessage = {
          role: 'assistant',
          content: data.response || data.error || 'I had trouble generating a response.',
          tools_used: data.tools_used,
          turn_id: data.turn_id,
          sequence_number: data.sequence_number,
          status: data.error ? 'failed' : 'completed',
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (data.error && !data.response) {
          setLastError(data.error);
        }
      }
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || 'Could not reach the AI service. Please try again.';
      setLastError(errMsg);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Sorry, I encountered an error: ${errMsg}`,
          status: 'failed',
        },
      ]);
    } finally {
      // Consume the idempotency key so the next message gets a fresh key.
      consumeIdempotencyKey(activeConversation?.id);
      setPendingIdempotencyKey(null);
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    if (!lastTurnId) return;
    setLoading(true);
    setLastError(null);
    try {
      const res = await aiService.retryTurn(lastTurnId);
      if (res.success && res.data) {
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: res.data.response || 'Retry completed.',
            tools_used: res.data.tools_used,
            status: 'completed',
          },
        ]);
        setLastTurnId(undefined);
      }
    } catch {
      setLastError('Retry failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    'Can you give me a hint?',
    'Explain this concept simply',
    'Show me a real-world example',
    'Why is this approach preferred?',
  ];

  return (
    <div
      className={`flex bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden ${
        compact ? 'h-[520px]' : 'h-[700px]'
      }`}
    >
      {/* Sidebar */}
      {sidebarOpen && !compact && (
        <div className="w-56 shrink-0 border-r border-slate-200 dark:border-slate-800">
          <ConversationSidebar
            activeConversationId={activeConversation?.id}
            onSelect={handleSelectConversation}
            onNew={handleNewConversation}
          />
        </div>
      )}

      {/* Main Chat Panel */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="p-3 bg-white dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-700/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            {!compact && (
              <button
                onClick={() => setSidebarOpen((v) => !v)}
                className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
                title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
              >
                {sidebarOpen ? (
                  <PanelLeftClose className="w-4 h-4" />
                ) : (
                  <PanelLeftOpen className="w-4 h-4" />
                )}
              </button>
            )}
            <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white flex items-center justify-center shadow-xs">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
                <span>AI Mentor</span>
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
              </h4>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                {activeConversation
                  ? (activeConversation.title || 'Learning Session')
                  : 'New Session'}
              </p>
            </div>
          </div>

          {lastTurnId && lastError && (
            <button
              onClick={handleRetry}
              disabled={loading}
              className="flex items-center gap-1 text-xs text-amber-600 hover:text-amber-700 px-2 py-1 rounded-lg bg-amber-50 dark:bg-amber-950/50 hover:bg-amber-100 transition-colors"
            >
              <RefreshCcw className="w-3 h-3" />
              Retry
            </button>
          )}
        </div>

        {/* Messages area */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {historyLoading && (
            <div className="flex items-center justify-center py-8 text-slate-400">
              <Sparkles className="w-5 h-5 animate-spin mr-2" />
              <span className="text-sm">Loading conversation history...</span>
            </div>
          )}

          {!historyLoading &&
            messages.map((msg, idx) => <ChatMessage key={idx} message={msg} />)}

          {loading && (
            <div className="flex items-center gap-2.5 text-xs text-slate-500 dark:text-slate-400 py-2">
              <div className="w-7 h-7 rounded-xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-600">
                <Sparkles className="w-4 h-4 animate-spin" />
              </div>
              <span>AI Mentor is thinking &amp; analyzing context...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick suggestions */}
        {!compact && (
          <div className="px-4 py-2 bg-white/50 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800 flex gap-2 overflow-x-auto no-scrollbar">
            {quickPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                disabled={loading}
                className="shrink-0 text-xs px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-indigo-50 hover:text-indigo-600 dark:hover:bg-indigo-950/60 dark:hover:text-indigo-400 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}

        {/* Input area */}
        <div className="p-3 bg-white dark:bg-slate-800/80 border-t border-slate-200 dark:border-slate-700/80 flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask AI Mentor anything..."
            disabled={loading}
            className="flex-1 px-3.5 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-slate-100"
          />
          <Button size="sm" onClick={() => handleSend()} disabled={!input.trim() || loading}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};
