import { LocalSearchClient, type SearchResult, type IndexName } from './local-search.js';
import { generateContent } from '../utils/gemini.js';
import { getSettings } from '../config.js';
import type { ToolResponse, Source, ResponseMetadata, ChartType } from '../types/schemas.js';

export interface ToolInvokeParams {
  userQuery: string;
  generateChart?: boolean;
  chartType?: ChartType;
}

/**
 * Base class for all RAG tools.
 * Provides common local FAISS search + Gemini RAG functionality.
 */
export abstract class BaseTool {
  // Override in subclasses to specify which index to use
  abstract readonly indexName: IndexName;
  abstract readonly systemPrompt: string;
  abstract readonly name: string;

  private searchClient: LocalSearchClient;

  constructor() {
    this.searchClient = LocalSearchClient.getInstance();
  }

  /**
   * Execute the tool with RAG pattern.
   */
  async invoke(params: ToolInvokeParams): Promise<ToolResponse> {
    const { userQuery, generateChart: shouldGenerateChart = false, chartType = 'bar' } = params;
    const settings = getSettings();

    // Track metadata for response
    const metadata: ResponseMetadata = {
      indexUsed: this.indexName,
      searchResultsCount: 0,
      dataStoreEmpty: false,
      usedInternalKnowledge: false,
    };

    // 1. Query topic-specific FAISS index
    let searchResults: SearchResult[];
    try {
      searchResults = await this.searchClient.search(this.indexName, userQuery);
    } catch (error) {
      console.error(`Error searching ${this.indexName} index:`, error);
      throw error;
    }

    // Update metadata with search results info
    metadata.searchResultsCount = searchResults.length;
    metadata.dataStoreEmpty = searchResults.length === 0;

    // 2. Build context from search results
    const context = this.searchClient.buildContext(searchResults);
    const sources = this.extractSources(searchResults);

    // 3. Generate response with Gemini
    const useInternalKnowledge =
      metadata.dataStoreEmpty && settings.allowGeneralKnowledgeFallback;
    metadata.usedInternalKnowledge = useInternalKnowledge;

    let reply: string;
    if (metadata.dataStoreEmpty && !settings.allowGeneralKnowledgeFallback) {
      reply =
        'No relevant documents were found in the knowledge base to answer your question. ' +
        'Please ensure documents have been uploaded and indexed.';
    } else {
      try {
        reply = await this.generateResponse(userQuery, context, useInternalKnowledge);
      } catch (error) {
        const errorStr = error instanceof Error ? error.message.toLowerCase() : '';
        if (errorStr.includes('overloaded') || errorStr.includes('503')) {
          reply = 'The AI model is currently overloaded. Please try again in a few moments.';
          metadata.warning = 'Gemini model overloaded';
        } else if (errorStr.includes('quota') || errorStr.includes('429')) {
          reply = 'API rate limit reached. Please try again later.';
          metadata.warning = 'API rate limit reached';
        } else {
          throw error;
        }
      }
    }

    // 4. Optionally generate chart
    let imageBase64: string | undefined;
    if (shouldGenerateChart) {
      try {
        // Dynamic import to avoid loading chart deps if not needed
        const { extractChartData } = await import('../charts/data-extractor.js');
        const { generateChart } = await import('../charts/generator.js');

        const chartData = await extractChartData(userQuery, context, chartType);
        if (chartData) {
          imageBase64 = await generateChart(chartData.data, chartData.title, chartType);
        }
      } catch (error) {
        console.warn(`Warning: Chart generation failed: ${error}`);
        metadata.warning = 'Chart generation failed';
      }
    }

    return {
      reply,
      chartType: shouldGenerateChart && imageBase64 ? chartType : undefined,
      imageBase64,
      sources,
      metadata,
    };
  }

  private async generateResponse(
    userQuery: string,
    context: string,
    useInternalKnowledge: boolean
  ): Promise<string> {
    let prompt: string;

    if (useInternalKnowledge) {
      prompt = `Answer the user's question using your internal knowledge.
Note: No documents were found in the knowledge base, so provide a general answer based on your training.
Start your response with a brief note that this answer is from general knowledge, not from specific documents.

User Question: ${userQuery}

Answer:`;
    } else {
      prompt = `Based on the following context from official documents, answer the user's question.
If the context doesn't contain enough information to answer the question, say so clearly.
Always cite which document(s) your answer is based on.

Context:
${context}

User Question: ${userQuery}

Answer:`;
    }

    return generateContent(prompt, this.systemPrompt);
  }

  private extractSources(results: SearchResult[]): Source[] {
    const sources: Source[] = [];
    const seenUrls = new Set<string>();

    for (const result of results) {
      if (result.pdfUrl && !seenUrls.has(result.pdfUrl)) {
        seenUrls.add(result.pdfUrl);
        sources.push({
          pdfName: result.pdfName,
          pdfUrl: result.pdfUrl,
          page: result.page,
          snippet: result.content?.slice(0, 200),
        });
      }
    }

    return sources;
  }
}
