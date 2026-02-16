'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { researchService } from '@/services/research';
import { useAuth } from '@/hooks/useAuth';
import { Search, BookOpen, ExternalLink, Bookmark, AlertCircle } from 'lucide-react';
import type { SearchResultsResponse, ResearchArticle } from '@/types';

export function ResearchView() {
  const { user, isLoading: isAuthLoading } = useAuth(true);
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedArticle, setSelectedArticle] = useState<ResearchArticle | null>(null);

  const searchMutation = useMutation({
    mutationFn: (searchQuery: string) =>
      researchService.searchLiterature({ query: searchQuery, max_results: 20 }),
    onSuccess: (data) => {
      setSearchResults(data);
      setError(null);
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Search failed';
      setError(msg);
      setSearchResults(null);
    },
  });

  const bookmarkMutation = useMutation({
    mutationFn: (articleId: string) =>
      researchService.bookmarkArticle({ article_id: articleId }),
    onSuccess: () => {
      setError(null);
      // Could show success toast here
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : 'Failed to bookmark article';
      setError(msg);
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      searchMutation.mutate(query);
    }
  };

  if (isAuthLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <BookOpen className="w-7 h-7" />
          Medical Literature Research
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Search PubMed and discover peer-reviewed research articles
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

      {/* Search Bar */}
      <Card>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-3 pt-6">
            <div className="flex-1">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search medical literature... (e.g., 'diabetes nutrition', 'sleep quality HRV')"
                className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-500 dark:placeholder-slate-400"
              />
            </div>
            <Button type="submit" disabled={searchMutation.isPending || !query.trim()}>
              <Search className="w-4 h-4 mr-2" />
              {searchMutation.isPending ? 'Searching...' : 'Search'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResults && (
        <div>
          <div className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            Found {searchResults.total_results} results for "{searchResults.query}"
          </div>

          {searchResults.articles.length === 0 ? (
            <Card>
              <CardContent className="text-center py-12">
                <div className="text-slate-500 dark:text-slate-400">
                  No articles found. Try a different search term.
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {searchResults.articles.map((article) => (
                <Card key={article.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
                          {article.title}
                        </h3>

                        {article.authors.length > 0 && (
                          <div className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                            {article.authors.slice(0, 3).join(', ')}
                            {article.authors.length > 3 && ` et al.`}
                          </div>
                        )}

                        {article.journal && article.publication_date && (
                          <div className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                            {article.journal} • {new Date(article.publication_date).getFullYear()}
                          </div>
                        )}

                        {article.abstract && (
                          <p className="text-sm text-slate-700 dark:text-slate-300 line-clamp-3 mb-3">
                            {article.abstract}
                          </p>
                        )}

                        {article.keywords.length > 0 && (
                          <div className="flex flex-wrap gap-2 mb-3">
                            {article.keywords.slice(0, 5).map((keyword, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-xs text-slate-700 dark:text-slate-300 rounded"
                              >
                                {keyword}
                              </span>
                            ))}
                          </div>
                        )}

                        <div className="flex gap-3">
                          {article.source_url && (
                            <a
                              href={article.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
                            >
                              View on PubMed
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                          {article.doi && (
                            <a
                              href={`https://doi.org/${article.doi}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
                            >
                              DOI
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedArticle(article)}
                        >
                          Details
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => bookmarkMutation.mutate(article.id)}
                          disabled={bookmarkMutation.isPending}
                        >
                          <Bookmark className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* No Search Yet */}
      {!searchResults && !searchMutation.isPending && (
        <Card>
          <CardContent className="text-center py-16">
            <BookOpen className="w-16 h-16 mx-auto mb-4 text-slate-400 dark:text-slate-600" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-2">
              Search Medical Literature
            </h3>
            <p className="text-slate-600 dark:text-slate-400 max-w-md mx-auto">
              Search millions of peer-reviewed research articles from PubMed. Find evidence-based
              information about health conditions, treatments, nutrition, and more.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Article Detail Modal */}
      {selectedArticle && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 pr-8">
                  {selectedArticle.title}
                </h2>
                <button
                  onClick={() => setSelectedArticle(null)}
                  className="text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 text-2xl"
                >
                  ×
                </button>
              </div>

              {selectedArticle.authors.length > 0 && (
                <div className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  <strong>Authors:</strong> {selectedArticle.authors.join(', ')}
                </div>
              )}

              {selectedArticle.journal && (
                <div className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  <strong>Journal:</strong> {selectedArticle.journal}
                  {selectedArticle.publication_date && (
                    <> • {new Date(selectedArticle.publication_date).toLocaleDateString()}</>
                  )}
                </div>
              )}

              {selectedArticle.pubmed_id && (
                <div className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  <strong>PMID:</strong> {selectedArticle.pubmed_id}
                </div>
              )}

              {selectedArticle.abstract && (
                <div className="mt-4">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
                    Abstract
                  </h3>
                  <p className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                    {selectedArticle.abstract}
                  </p>
                </div>
              )}

              {selectedArticle.keywords.length > 0 && (
                <div className="mt-4">
                  <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
                    Keywords
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedArticle.keywords.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-slate-100 dark:bg-slate-700 text-sm text-slate-700 dark:text-slate-300 rounded"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3 mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
                {selectedArticle.source_url && (
                  <a
                    href={selectedArticle.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1"
                  >
                    <Button className="w-full">
                      View on PubMed
                      <ExternalLink className="w-4 h-4 ml-2" />
                    </Button>
                  </a>
                )}
                <Button
                  variant="outline"
                  onClick={() => {
                    bookmarkMutation.mutate(selectedArticle.id);
                    setSelectedArticle(null);
                  }}
                  disabled={bookmarkMutation.isPending}
                >
                  <Bookmark className="w-4 h-4 mr-2" />
                  Bookmark
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
