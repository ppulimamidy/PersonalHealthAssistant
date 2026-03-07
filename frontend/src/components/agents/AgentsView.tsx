'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { agentsService } from '@/services/agents';
import { useAuth } from '@/hooks/useAuth';
import { Bot, Send, User, Sparkles, AlertCircle } from 'lucide-react';
import type { AgentInfo, ChatMessage } from '@/types';

// Sample questions shown in empty state per agent type
const SAMPLE_QUESTIONS: Record<string, string[]> = {
  nutrition_analyst: [
    'Create a 7-day meal plan for weight loss',
    'What foods help reduce inflammation?',
    'Analyze my recent eating patterns',
  ],
  health_coach: [
    'Help me build a sustainable morning routine',
    'What habits should I prioritize first?',
    'Create a beginner workout schedule for me',
  ],
  symptom_investigator: [
    'I have recurring afternoon headaches — what could cause this?',
    'Help me find patterns in my recent symptoms',
    'Why might I be feeling fatigued after meals?',
  ],
  research_assistant: [
    'What does research say about intermittent fasting?',
    'Find evidence on vitamin D and immune function',
    'Summarize the latest findings on sleep quality',
  ],
  medication_advisor: [
    'Are there interactions between my current medications?',
    'What is the best time to take my supplements?',
    'Explain the common side effects of metformin',
  ],
};

// Render inline markdown: **bold**, *italic*, `code`
function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
          return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
          return <em key={i}>{part.slice(1, -1)}</em>;
        }
        if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
          return (
            <code key={i} className="bg-slate-200 dark:bg-slate-700 px-1 py-0.5 rounded text-xs font-mono">
              {part.slice(1, -1)}
            </code>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

// Render markdown content into styled JSX elements
function renderMarkdown(content: string): React.ReactNode {
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listType: 'ul' | 'ol' | null = null;
  let inCodeBlock = false;
  let codeLines: string[] = [];

  const flushList = (key: string) => {
    if (listItems.length === 0) return;
    if (listType === 'ul') {
      elements.push(
        <ul key={key} className="list-disc list-outside ml-5 space-y-1 my-2">
          {listItems.map((item, i) => (
            <li key={i} className="text-sm leading-relaxed">{renderInline(item)}</li>
          ))}
        </ul>
      );
    } else {
      elements.push(
        <ol key={key} className="list-decimal list-outside ml-5 space-y-1 my-2">
          {listItems.map((item, i) => (
            <li key={i} className="text-sm leading-relaxed">{renderInline(item)}</li>
          ))}
        </ol>
      );
    }
    listItems = [];
    listType = null;
  };

  lines.forEach((line, i) => {
    // Code block toggling
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${i}`} className="bg-slate-900 dark:bg-slate-950 text-green-400 rounded-lg p-3 text-xs overflow-x-auto my-2 font-mono leading-relaxed">
            <code>{codeLines.join('\n')}</code>
          </pre>
        );
        codeLines = [];
        inCodeBlock = false;
      } else {
        flushList(`list-${i}`);
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      return;
    }

    if (line.startsWith('### ')) {
      flushList(`list-${i}`);
      elements.push(
        <h3 key={i} className="font-semibold text-sm mt-3 mb-1 text-slate-900 dark:text-slate-100">
          {renderInline(line.slice(4))}
        </h3>
      );
    } else if (line.startsWith('## ')) {
      flushList(`list-${i}`);
      elements.push(
        <h2 key={i} className="font-bold text-base mt-4 mb-2 text-slate-900 dark:text-slate-100">
          {renderInline(line.slice(3))}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      flushList(`list-${i}`);
      elements.push(
        <h1 key={i} className="font-bold text-lg mt-4 mb-2 text-slate-900 dark:text-slate-100">
          {renderInline(line.slice(2))}
        </h1>
      );
    } else if (line === '---' || line === '* * *') {
      flushList(`list-${i}`);
      elements.push(<hr key={i} className="border-slate-300 dark:border-slate-600 my-3" />);
    } else if (/^[-*] /.test(line)) {
      if (listType !== 'ul') {
        flushList(`list-${i}`);
        listType = 'ul';
      }
      listItems.push(line.slice(2));
    } else if (/^\d+\. /.test(line)) {
      if (listType !== 'ol') {
        flushList(`list-${i}`);
        listType = 'ol';
      }
      listItems.push(line.replace(/^\d+\. /, ''));
    } else if (line.trim() === '') {
      flushList(`list-${i}`);
      if (elements.length > 0) {
        elements.push(<div key={`gap-${i}`} className="h-1" />);
      }
    } else {
      flushList(`list-${i}`);
      elements.push(
        <p key={i} className="text-sm leading-relaxed">
          {renderInline(line)}
        </p>
      );
    }
  });

  flushList('final-list');

  return <div className="space-y-0.5">{elements}</div>;
}

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
  const { data: conversation } = useQuery({
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

  const handleSend = (text?: string) => {
    const toSend = text ?? message;
    if (!toSend.trim() || sendMessageMutation.isPending) return;
    if (text) setMessage('');
    sendMessageMutation.mutate(toSend);
  };

  const handleSampleQuestion = (q: string) => {
    if (!selectedAgent || sendMessageMutation.isPending) return;
    handleSend(q);
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
  const sampleQuestions = selectedAgent ? (SAMPLE_QUESTIONS[selectedAgent] ?? []) : [];
  const hasMessages = conversation && conversation.messages.length > 0;

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
                    onClick={() => {
                      setSelectedAgent(agent.agent_type);
                      setActiveConversation(null);
                    }}
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
            <CardContent className="flex-1 flex flex-col p-0 min-h-0">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4 min-h-0">
                {!hasMessages ? (
                  <div className="text-center py-8">
                    <Bot className="w-16 h-16 mx-auto mb-4 text-slate-400 dark:text-slate-600" />
                    {selectedAgent ? (
                      <>
                        <p className="text-slate-600 dark:text-slate-400 mb-6">
                          Start a conversation below, or try one of these:
                        </p>
                        <div className="flex flex-col gap-2 items-center">
                          {sampleQuestions.map((q) => (
                            <button
                              key={q}
                              onClick={() => handleSampleQuestion(q)}
                              disabled={sendMessageMutation.isPending}
                              className="w-full max-w-sm text-sm px-4 py-2.5 rounded-xl border border-primary-300 dark:border-primary-700 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 hover:bg-primary-100 dark:hover:bg-primary-900/40 transition-colors text-left leading-snug disabled:opacity-50"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </>
                    ) : (
                      <p className="text-slate-600 dark:text-slate-400">
                        Select an agent from the left to begin
                      </p>
                    )}
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
                        {msg.role === 'assistant'
                          ? renderMarkdown(msg.content)
                          : <p className="text-sm leading-relaxed">{msg.content}</p>
                        }
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {sendMessageMutation.isPending && (
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-slate-200 dark:bg-slate-700">
                      <Bot className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                    </div>
                    <div className="flex-1 p-4 rounded-lg bg-slate-100 dark:bg-slate-800">
                      <div className="flex gap-1 items-center">
                        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
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
                    onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                    placeholder={
                      selectedAgent
                        ? 'Type your message...'
                        : 'Select an agent first...'
                    }
                    disabled={!selectedAgent || sendMessageMutation.isPending}
                    className="flex-1 px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400"
                  />
                  <Button
                    onClick={() => handleSend()}
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
