import React, { useState, useEffect, useCallback } from 'react';
import { AIConversation } from '../../types';
import { aiService } from '../../services/ai';
import { Button } from '../ui/Button';
import {
  MessageSquare,
  Plus,
  Pencil,
  Trash2,
  Loader,
  AlertCircle,
} from 'lucide-react';

interface ConversationSidebarProps {
  activeConversationId?: string;
  onSelect: (conv: AIConversation) => void;
  onNew: () => void;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  activeConversationId,
  onSelect,
  onNew,
}) => {
  const [conversations, setConversations] = useState<AIConversation[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await aiService.listConversations(30, 0);
      if (res.success) {
        setConversations(res.data.items);
        setTotal(res.data.total);
      }
    } catch {
      setError('Failed to load conversations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const handleRenameSubmit = async (conv: AIConversation) => {
    if (!renameValue.trim()) return;
    try {
      await aiService.renameConversation(conv.id, renameValue.trim());
      setConversations((prev) =>
        prev.map((c) => (c.id === conv.id ? { ...c, title: renameValue.trim() } : c))
      );
    } catch {
      /* noop */
    } finally {
      setRenamingId(null);
    }
  };

  const handleDelete = async (conv: AIConversation) => {
    setDeletingId(conv.id);
    try {
      await aiService.deleteConversation(conv.id);
      setConversations((prev) => prev.filter((c) => c.id !== conv.id));
      setTotal((t) => t - 1);
      if (conv.id === activeConversationId) {
        onNew();
      }
    } catch {
      /* noop */
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <aside className="flex flex-col w-full h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
      {/* Header */}
      <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          Conversations
        </span>
        <button
          onClick={onNew}
          className="p-1.5 rounded-lg text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950 transition-colors"
          title="New conversation"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto py-1">
        {loading && (
          <div className="flex justify-center py-6 text-slate-400">
            <Loader className="w-5 h-5 animate-spin" />
          </div>
        )}

        {error && !loading && (
          <div className="flex flex-col items-center py-6 gap-2 text-slate-400">
            <AlertCircle className="w-5 h-5 text-rose-400" />
            <p className="text-xs text-center px-4">{error}</p>
            <button
              onClick={loadConversations}
              className="text-xs text-indigo-500 hover:underline"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && conversations.length === 0 && (
          <div className="flex flex-col items-center py-8 gap-2 text-slate-400">
            <MessageSquare className="w-6 h-6" />
            <p className="text-xs text-center px-4">No conversations yet. Start a new session!</p>
          </div>
        )}

        {conversations.map((conv) => (
          <div
            key={conv.id}
            className={`group relative flex items-center gap-2 px-3 py-2.5 cursor-pointer rounded-lg mx-1 my-0.5 transition-colors ${
              conv.id === activeConversationId
                ? 'bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300'
                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
            onClick={() => renamingId !== conv.id && onSelect(conv)}
          >
            <MessageSquare className="w-3.5 h-3.5 shrink-0 opacity-50" />

            {renamingId === conv.id ? (
              <input
                autoFocus
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onBlur={() => handleRenameSubmit(conv)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRenameSubmit(conv);
                  if (e.key === 'Escape') setRenamingId(null);
                }}
                onClick={(e) => e.stopPropagation()}
                className="flex-1 text-xs bg-white dark:bg-slate-800 border border-indigo-400 rounded px-1.5 py-0.5 outline-none"
              />
            ) : (
              <span className="flex-1 text-xs font-medium truncate">
                {conv.title || 'Learning Session'}
              </span>
            )}

            {/* Action buttons - shown on hover */}
            {renamingId !== conv.id && (
              <div className="hidden group-hover:flex items-center gap-1 ml-auto shrink-0">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setRenamingId(conv.id);
                    setRenameValue(conv.title || '');
                  }}
                  className="p-1 rounded hover:bg-indigo-100 dark:hover:bg-indigo-900 text-slate-400 hover:text-indigo-600"
                  title="Rename"
                >
                  <Pencil className="w-3 h-3" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(conv);
                  }}
                  disabled={deletingId === conv.id}
                  className="p-1 rounded hover:bg-rose-100 dark:hover:bg-rose-900 text-slate-400 hover:text-rose-500"
                  title="Delete"
                >
                  {deletingId === conv.id ? (
                    <Loader className="w-3 h-3 animate-spin" />
                  ) : (
                    <Trash2 className="w-3 h-3" />
                  )}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {total > conversations.length && (
        <div className="p-2 border-t border-slate-100 dark:border-slate-800">
          <p className="text-center text-xs text-slate-400">
            Showing {conversations.length} of {total}
          </p>
        </div>
      )}
    </aside>
  );
};
