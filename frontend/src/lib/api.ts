/**
 * API client for research agent backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ResearchRequest {
  query: string;
  domain: 'tech' | 'investing';
  depth: 'quick' | 'standard' | 'deep';
}

export interface ResearchStartResponse {
  research_id: string;
  message: string;
  status: string;
}

export interface ResearchStatus {
  research_id: string;
  status: string;
  progress: number;
  current_stage: string;
  sources_collected: number;
  iteration: number;
  error_message?: string;
}

export interface Source {
  url: string;
  title: string;
  snippet: string;
  source_type: string;
  credibility_score: number;
}

export interface ResearchResult {
  research_id: string;
  query: string;
  domain: string;
  depth: string;
  report: string;
  sources: Source[];
  confidence_score: number;
  completed_at: string;
}

/**
 * Start a new research task
 */
export async function startResearch(request: ResearchRequest): Promise<ResearchStartResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to start research: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get status of a research task
 */
export async function getResearchStatus(researchId: string): Promise<ResearchStatus> {
  const response = await fetch(`${API_BASE_URL}/api/research/status/${researchId}`);

  if (!response.ok) {
    throw new Error(`Failed to get research status: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get final research result
 */
export async function getResearchResult(researchId: string): Promise<ResearchResult> {
  const response = await fetch(`${API_BASE_URL}/api/research/result/${researchId}`);

  if (!response.ok) {
    throw new Error(`Failed to get research result: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Poll for research completion
 */
export async function pollResearchCompletion(
  researchId: string,
  onProgress?: (status: ResearchStatus) => void
): Promise<ResearchResult> {
  const maxAttempts = 120; // 4 minutes max
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getResearchStatus(researchId);

    if (onProgress) {
      onProgress(status);
    }

    if (status.status === 'completed') {
      return await getResearchResult(researchId);
    }

    if (status.status === 'failed') {
      throw new Error(status.error_message || 'Research failed');
    }

    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
    attempts++;
  }

  throw new Error('Research timeout');
}
