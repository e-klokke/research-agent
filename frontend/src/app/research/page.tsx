'use client';

import { useState } from 'react';
import ResearchInput from '@/components/ResearchInput';
import ProgressTracker from '@/components/ProgressTracker';
import ResultsDisplay from '@/components/ResultsDisplay';
import { startResearch, pollResearchCompletion, ResearchStatus, ResearchResult } from '@/lib/api';

export default function ResearchPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<ResearchStatus | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleResearch = async (
    query: string,
    domain: 'tech' | 'investing',
    depth: 'quick' | 'standard' | 'deep'
  ) => {
    try {
      setIsLoading(true);
      setStatus(null);
      setResult(null);
      setError(null);

      // Start research
      const startResponse = await startResearch({ query, domain, depth });
      console.log('Research started:', startResponse);

      // Poll for completion
      const finalResult = await pollResearchCompletion(
        startResponse.research_id,
        (progressStatus) => {
          console.log('Progress:', progressStatus);
          setStatus(progressStatus);
        }
      );

      console.log('Research completed:', finalResult);
      setResult(finalResult);
      setStatus(null);

    } catch (err) {
      console.error('Research error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Research Agent
          </h1>
          <p className="text-lg text-gray-600">
            AI-powered intelligence for technology and investing research
          </p>
        </div>

        {/* Input */}
        <ResearchInput onSubmit={handleResearch} isLoading={isLoading} />

        {/* Progress */}
        {isLoading && <ProgressTracker status={status} />}

        {/* Error */}
        {error && (
          <div className="w-full max-w-4xl mx-auto p-6 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="text-lg font-semibold text-red-800 mb-2">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && <ResultsDisplay result={result} />}

        {/* Sample Queries */}
        {!isLoading && !result && (
          <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Sample Queries
            </h3>
            <div className="space-y-2">
              <div className="text-sm">
                <strong className="text-gray-700">Tech:</strong>
                <ul className="list-disc ml-6 mt-1 text-gray-600">
                  <li>Compare Kubernetes vs Docker Swarm for enterprise deployment</li>
                  <li>Evaluate zero-trust architecture solutions for hybrid cloud</li>
                  <li>What are the security considerations for implementing GraphQL APIs?</li>
                </ul>
              </div>
              <div className="text-sm mt-4">
                <strong className="text-gray-700">Investing:</strong>
                <ul className="list-disc ml-6 mt-1 text-gray-600">
                  <li>Analyze Tesla fundamentals and growth prospects</li>
                  <li>Compare NVIDIA vs AMD for AI chip investment</li>
                  <li>What are the risks in high-yield bond market?</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
