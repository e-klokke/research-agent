'use client';

import { useState, useEffect } from 'react';
import { getResearchHistory, deleteResearch, HistoryItem } from '@/lib/api';

interface HistoryPanelProps {
  onSelectResearch: (researchId: string) => void;
}

export default function HistoryPanel({ onSelectResearch }: HistoryPanelProps) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getResearchHistory(20);
      setHistory(response.history);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleDelete = async (researchId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm('Delete this research from history?')) {
      return;
    }

    try {
      await deleteResearch(researchId);
      setHistory(prev => prev.filter(item => item.research_id !== researchId));
    } catch (err) {
      alert('Failed to delete research');
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Research History</h2>
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Research History</h2>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold">Research History</h2>
        <button
          onClick={loadHistory}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Refresh
        </button>
      </div>

      {history.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No research history yet</p>
      ) : (
        <div className="space-y-3">
          {history.map((item) => (
            <div
              key={item.research_id}
              onClick={() => onSelectResearch(item.research_id)}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-gray-900 flex-1 pr-4">
                  {item.query}
                </h3>
                <button
                  onClick={(e) => handleDelete(item.research_id, e)}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  Delete
                </button>
              </div>
              <div className="flex gap-2 text-sm text-gray-600">
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded">
                  {item.domain}
                </span>
                <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                  {item.depth}
                </span>
                {item.completed && (
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                    ✓ Completed
                  </span>
                )}
                {!item.completed && (
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded">
                    Failed
                  </span>
                )}
              </div>
              {item.completed && (
                <div className="mt-2 text-sm text-gray-500">
                  Confidence: {(item.confidence_score * 10).toFixed(1)}/10
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
