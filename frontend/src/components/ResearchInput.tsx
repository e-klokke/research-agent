'use client';

import { useState } from 'react';

interface ResearchInputProps {
  onSubmit: (query: string, domain: 'tech' | 'investing', depth: 'quick' | 'standard' | 'deep') => void;
  isLoading: boolean;
}

export default function ResearchInput({ onSubmit, isLoading }: ResearchInputProps) {
  const [query, setQuery] = useState('');
  const [domain, setDomain] = useState<'tech' | 'investing'>('tech');
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query, domain, depth);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Research Query
          </label>
          <textarea
            id="query"
            rows={3}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="e.g., Compare Kubernetes vs Docker Swarm for enterprise deployment"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-2">
              Domain
            </label>
            <select
              id="domain"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={domain}
              onChange={(e) => setDomain(e.target.value as 'tech' | 'investing')}
              disabled={isLoading}
            >
              <option value="tech">Technology</option>
              <option value="investing">Investing</option>
            </select>
          </div>

          <div>
            <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
              Research Depth
            </label>
            <select
              id="depth"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={depth}
              onChange={(e) => setDepth(e.target.value as 'quick' | 'standard' | 'deep')}
              disabled={isLoading}
            >
              <option value="quick">Quick (30-60s)</option>
              <option value="standard">Standard (1-2 min)</option>
              <option value="deep">Deep (2-4 min)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="w-full py-3 px-6 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Researching...' : 'Start Research'}
        </button>
      </form>
    </div>
  );
}
