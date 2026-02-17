'use client';

import { api } from './api';
import type {
  AgentInfo,
  AgentConversation,
  SendMessageRequest,
  AgentAction,
} from '@/types';

export const agentsService = {
  // Agents
  listAgents: async (): Promise<AgentInfo[]> => {
    const response = await api.get('/api/v1/agents/agents');
    return response.data;
  },

  // Chat
  sendMessage: async (request: SendMessageRequest): Promise<AgentConversation> => {
    const response = await api.post('/api/v1/agents/chat', request);
    return response.data;
  },

  // Conversations
  listConversations: async (): Promise<AgentConversation[]> => {
    const response = await api.get('/api/v1/agents/conversations');
    return response.data;
  },

  getConversation: async (conversationId: string): Promise<AgentConversation> => {
    const response = await api.get(`/api/v1/agents/conversations/${conversationId}`);
    return response.data;
  },

  // Actions
  listActions: async (status?: string): Promise<AgentAction[]> => {
    const response = await api.get('/api/v1/agents/actions', {
      params: status ? { status } : {},
    });
    return response.data;
  },

  updateAction: async (
    actionId: string,
    status: string,
    feedback?: string
  ): Promise<AgentAction> => {
    const response = await api.patch(`/api/v1/agents/actions/${actionId}`, {
      status,
      user_feedback: feedback,
    });
    return response.data;
  },
};
