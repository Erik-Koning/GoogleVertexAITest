import type { ChatResponse } from '../types/schemas.js';

export function formatErrorResponse(errorMessage: string): ChatResponse {
  return {
    reply: `I apologize, but I encountered an error: ${errorMessage}. Please try again.`,
    sources: [],
  };
}

export function formatNoResultsResponse(query: string): ChatResponse {
  return {
    reply:
      `I couldn't find relevant information for your query: '${query}'. ` +
      'Please try rephrasing your question or ask about TFSA, RRSP, or Fund Facts topics.',
    sources: [],
  };
}
