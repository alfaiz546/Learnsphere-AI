import api from './api';
import { AIConversation } from '../types';

// ---------------------------------------------------------------------------
// Idempotency key management (per logical chat submission)
// ---------------------------------------------------------------------------
// A stable UUID is generated for each logical message submission. The same
// key is reused for retries of that submission, and a new key is generated
// for each distinct message. This enables exactly-once chat semantics on the
// backend.
const pendingIdempotencyKeys = new Map<string, string>(); // conversationId -> key

export function generateIdempotencyKey(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export function getIdempotencyKey(conversationId?: string): string | undefined {
  if (!conversationId) return undefined;
  return pendingIdempotencyKeys.get(conversationId);
}

export function setIdempotencyKey(conversationId: string, key: string): void {
  pendingIdempotencyKeys.set(conversationId, key);
}

export function consumeIdempotencyKey(conversationId?: string): void {
  if (conversationId) pendingIdempotencyKeys.delete(conversationId);
}

export const aiService = {
  // ---------------------------------------------------------------------------
  // Conversation Management
  // ---------------------------------------------------------------------------
  async createConversation(params?: {
    title?: string;
    context_type?: string;
    context_id?: string;
  }) {
    const res = await api.post('/ai/conversations', params || {});
    return res.data;
  },

  async listConversations(limit = 20, offset = 0) {
    const res = await api.get('/ai/conversations', { params: { limit, offset } });
    return res.data;
  },

  async getConversationHistory(conversationId: string, limit = 50, offset = 0) {
    const res = await api.get(`/ai/conversations/${conversationId}`, {
      params: { limit, offset },
    });
    return res.data;
  },

  async renameConversation(conversationId: string, title: string) {
    const res = await api.patch(`/ai/conversations/${conversationId}`, { title });
    return res.data;
  },

  async getDeletionToken(conversationId: string) {
    const res = await api.post(`/ai/conversations/${conversationId}/deletion-token`);
    return res.data;
  },

  async deleteConversation(conversationId: string, tokenData?: any) {
    const res = await api.delete(`/ai/conversations/${conversationId}`, {
      data: tokenData ?? undefined,
    });
    return res.data;
  },

  async retryTurn(turnId: string) {
    const res = await api.post(`/ai/turns/${turnId}/retry`);
    return res.data;
  },

  // ---------------------------------------------------------------------------
  // Core Chat
  // ---------------------------------------------------------------------------
  async chat(
    message: string,
    context?: any,
    conversationId?: string,
    idempotencyKey?: string,
  ) {
    const res = await api.post('/ai/chat', {
      message,
      context,
      conversation_id: conversationId,
      idempotency_key: idempotencyKey,
    });
    return res.data;
  },

  async getHint(questionId: string, studentAnswer?: string, lessonId?: string) {
    const res = await api.post('/ai/hint', {
      question_id: questionId,
      student_answer: studentAnswer,
      lesson_id: lessonId,
    });
    return res.data;
  },

  async analyzeWeaknesses(timePeriodDays: number = 30) {
    const res = await api.post('/ai/analyze', { time_period_days: timePeriodDays });
    return res.data;
  },

  async generateStudyPlan(data: {
    goal: string;
    available_hours_per_day: number;
    duration_days: number;
  }) {
    const res = await api.post('/ai/study-plan', data);
    return res.data;
  },

  async getCurrentStudyPlan() {
    const res = await api.get('/ai/study-plan/current');
    return res.data;
  },
};
