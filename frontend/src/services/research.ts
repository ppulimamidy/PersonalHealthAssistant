'use client';

import { api } from './api';
import type {
  PubMedSearchRequest,
  SearchResultsResponse,
  ResearchArticle,
  ArticleBookmark,
  BookmarkArticleRequest,
  RAGConversation,
  RAGMessageRequest,
  ResearchInsight,
  ResearchInsightRequest,
} from '@/types';

export const researchService = {
  // Search
  searchLiterature: async (request: PubMedSearchRequest): Promise<SearchResultsResponse> => {
    const response = await api.post('/api/v1/research/search', request);
    return response.data;
  },

  // Articles
  getArticle: async (articleId: string): Promise<ResearchArticle> => {
    const response = await api.get(`/api/v1/research/articles/${articleId}`);
    return response.data;
  },

  // Bookmarks
  bookmarkArticle: async (request: BookmarkArticleRequest): Promise<ArticleBookmark> => {
    const response = await api.post('/api/v1/research/bookmarks', request);
    return response.data;
  },

  listBookmarks: async (): Promise<ArticleBookmark[]> => {
    const response = await api.get('/api/v1/research/bookmarks');
    return response.data;
  },

  // RAG Chat
  ragChat: async (request: RAGMessageRequest): Promise<RAGConversation> => {
    const response = await api.post('/api/v1/research/rag/chat', request);
    return response.data;
  },

  // Insights
  generateInsight: async (request: ResearchInsightRequest): Promise<ResearchInsight> => {
    const response = await api.post('/api/v1/research/insights/generate', request);
    return response.data;
  },
};
