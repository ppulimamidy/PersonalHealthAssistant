'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { agentsService } from '@/services/agents';
import { useAuth } from '@/hooks/useAuth';
import { Bot, Send, User, Sparkles, AlertCircle } from 'lucide-react';
import type { AgentInfo, AgentConversation, ChatMessage } from '@/types';

export function AgentsView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const queryClient = useQueryClient();
  const [message, setMessage] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch available agents
  const { data: agents, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsService.listAgents(),
    enabled: Boolean(user) && !isAuthLoading,
  });

  // Fetch current conversation
  const { data: conversation, isLoading: conversationLoading } = useQuery({
    queryKey: ['conversation', activeConversation],
    queryFn: () => agentsService.getConversation(activeConversation!),
    enabled: Boolean(activeConversation),
    refetchInterval: false,
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (msg: string) =>
      agentsService.sendMessage({
        conversation_id: activeConversation || undefined,
        message: msg,
        agent_type: selectedAgent || undefined,
        conversation_type: 'general',
      }),
    onSuccess: (data) => {
      setActiveConversation(data.id);
      setMessage('');
      setError(null);
      queryClient.setQueryData(['conversation', data.id], data);
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Failed to send message';
      setError(msg);
    },
  });

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  const handleSend = () => {
    if (!message.trim() || sendMessageMutation.isPending) return;
    sendMessageMutation.mutate(message);
  };

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'health_coach':
        return '🏥';
      case 'nutrition_analyst':
        return '🥗';
      case 'symptom_investigator':
        return '🔬';
      case 'research_assistant':
        return '📚';
      case 'medication_advisor':
        return '💊';
      default:
        return '🤖';
    }
  };

  if (isAuthLoading || agentsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading AI agents...</div>
      </div>
    );
  }

  const agentsList = agents || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Sparkles className="w-7 h-7 text-primary-600 dark:text-primary-400" />
          AI Health Agents
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Chat with specialized AI assistants for personalized health insights
        </p>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Agent Selector */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Select an Agent</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {agentsList.map((agent: AgentInfo) => (
                  <button
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent.agent_type)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedAgent === agent.agent_type
                        ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-600 dark:border-primary-400'
                        : 'border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">{getAgentIcon(agent.agent_type)}</span>
                      <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                        {agent.agent_name}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {agent.agent_description}
                    </p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chat Interface */}
        <div className="lg:col-span-3">
          <Card className="h-[600px] flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                {selectedAgent
                  ? agentsList.find((a: AgentInfo) => a.agent_type === selectedAgent)?.agent_name ||
                    'AI Assistant'
                  : 'Select an agent to start chatting'}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col p-0">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {!conversation || conversation.messages.length === 0 ? (
                  <div className="text-center py-12">
                    <Bot className="w-16 h-16 mx-auto mb-4 text-slate-400 dark:text-slate-600" />
                    <p className="text-slate-600 dark:text-slate-400">
                      {selectedAgent
                        ? 'Start a conversation by sending a message below'
                        : 'Select an agent from the left to begin'}
                    </p>
                  </div>
                ) : (
                  conversation.messages.map((msg: ChatMessage, idx: number) => (
                    <div
                      key={idx}
                      className={`flex items-start gap-3 ${
                        msg.role === 'user' ? 'flex-row-reverse' : ''
                      }`}
                    >
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                          msg.role === 'user'
                            ? 'bg-primary-600 dark:bg-primary-400'
                            : 'bg-slate-200 dark:bg-slate-700'
                        }`}
                      >
                        {msg.role === 'user' ? (
                          <User className="w-4 h-4 text-white" />
                        ) : (
                          <Bot className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                        )}
                      </div>
                      <div
                        className={`flex-1 p-4 rounded-lg ${
                          msg.role === 'user'
                            ? 'bg-primary-100 dark:bg-primary-900/30 text-slate-900 dark:text-slate-100'
                            : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                        }`}
                      >
                        <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-slate-200 dark:border-slate-700 p-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder={
                      selectedAgent
                        ? 'Type your message...'
                        : 'Select an agent first...'
                    }
                    disabled={!selectedAgent || sendMessageMutation.isPending}
                    className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 disabled:opacity-50"
                  />
                  <Button
                    onClick={handleSend}
                    disabled={!message.trim() || !selectedAgent || sendMessageMutation.isPending}
                  >
                    {sendMessageMutation.isPending ? (
                      'Sending...'
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-1" />
                        Send
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
