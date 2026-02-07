'use client';

import { useState } from 'react';
import { ResearchResult, exportResearch } from '@/lib/api';

interface ResultsDisplayProps {
  result: ResearchResult | null;
}

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  const [exporting, setExporting] = useState(false);

  if (!result) return null;

  const handleExport = async (format: 'json' | 'markdown') => {
    try {
      setExporting(true);
      const data = await exportResearch(result.research_id, format);

      // Download the file
      const blob = new Blob(
        [format === 'json' ? JSON.stringify(data, null, 2) : data.content],
        { type: format === 'json' ? 'application/json' : 'text/markdown' }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `research-${result.research_id.slice(0, 8)}.${format === 'json' ? 'json' : 'md'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export research');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Research Report
            </h2>
            <p className="text-gray-600">{result.query}</p>
          </div>
          <div className="text-right ml-4">
            <div className="text-sm text-gray-500">Confidence</div>
            <div className="text-2xl font-bold text-blue-600">
              {(result.confidence_score * 10).toFixed(1)}/10
            </div>
          </div>
        </div>
        <div className="flex justify-between items-center">
          <div className="flex gap-4 text-sm text-gray-600">
            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
              {result.domain}
            </span>
            <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">
              {result.depth}
            </span>
            <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full">
              {result.sources.length} sources
            </span>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleExport('json')}
              disabled={exporting}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              Export JSON
            </button>
            <button
              onClick={() => handleExport('markdown')}
              disabled={exporting}
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded hover:bg-green-700 disabled:bg-gray-400 transition-colors"
            >
              Export MD
            </button>
          </div>
        </div>
      </div>

      {/* Report */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div
          className="prose max-w-none"
          dangerouslySetInnerHTML={{
            __html: formatMarkdown(result.report)
          }}
        />
      </div>

      {/* Sources */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          Top Sources ({result.sources.length})
        </h3>
        <div className="space-y-4">
          {result.sources.map((source, index) => (
            <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 font-medium"
              >
                {source.title}
              </a>
              <div className="text-sm text-gray-600 mt-1">
                {source.snippet}
              </div>
              <div className="flex gap-3 mt-2 text-xs text-gray-500">
                <span className="px-2 py-1 bg-gray-100 rounded">
                  {source.source_type}
                </span>
                <span>
                  Credibility: {(source.credibility_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function formatMarkdown(text: string): string {
  // Simple markdown to HTML conversion
  let html = text;

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold mt-6 mb-3">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold mt-8 mb-4">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold mt-8 mb-4">$1</h1>');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Lists
  html = html.replace(/^\* (.*$)/gim, '<li class="ml-4">$1</li>');
  html = html.replace(/^- (.*$)/gim, '<li class="ml-4">$1</li>');

  // Wrap lists
  html = html.replace(/(<li.*<\/li>)/s, '<ul class="list-disc ml-6 my-2">$1</ul>');

  // Paragraphs
  html = html.split('\n\n').map(para => {
    if (!para.startsWith('<')) {
      return `<p class="my-3">${para}</p>`;
    }
    return para;
  }).join('\n');

  return html;
}
