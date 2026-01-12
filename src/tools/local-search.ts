import { FaissStore } from '@langchain/community/vectorstores/faiss';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { getSettings } from '../config.js';

export type IndexName = 'tfsa' | 'rrsp' | 'fund_facts';

export interface SearchResult {
  content: string;
  pdfName: string;
  pdfUrl: string;
  page?: number;
  relevanceScore: number;
}

/**
 * Client for querying topic-specific FAISS vector stores.
 * Each topic (tfsa, rrsp, fund_facts) has its own index.
 */
export class LocalSearchClient {
  private static instance: LocalSearchClient | null = null;
  private static vectorstores: Map<IndexName, FaissStore> = new Map();
  private static loadingIndexes: Set<IndexName> = new Set();

  private constructor() {}

  static getInstance(): LocalSearchClient {
    if (!LocalSearchClient.instance) {
      LocalSearchClient.instance = new LocalSearchClient();
    }
    return LocalSearchClient.instance;
  }

  private async loadIndex(indexName: IndexName): Promise<FaissStore> {
    // Return cached if available
    const cached = LocalSearchClient.vectorstores.get(indexName);
    if (cached) return cached;

    // Wait if already loading
    if (LocalSearchClient.loadingIndexes.has(indexName)) {
      while (LocalSearchClient.loadingIndexes.has(indexName)) {
        await new Promise((resolve) => setTimeout(resolve, 100));
      }
      const loaded = LocalSearchClient.vectorstores.get(indexName);
      if (loaded) return loaded;
    }

    LocalSearchClient.loadingIndexes.add(indexName);

    try {
      const settings = getSettings();
      const indexPath = join(settings.faissIndexBasePath, indexName);

      if (!existsSync(indexPath)) {
        throw new Error(
          `FAISS index not found at: ${indexPath}\n` +
            `Please ensure the ${indexName} index exists at FAISS_INDEX_BASE_PATH/${indexName}`
        );
      }

      // Load FAISS index
      // Note: We need to provide embeddings even though they're stored in the index
      // This is a LangChain requirement - we provide a dummy embeddings object
      const dummyEmbeddings = {
        embedDocuments: async (_documents: string[]) => [] as number[][],
        embedQuery: async (_text: string) => [] as number[],
      };

      const vectorstore = await FaissStore.load(indexPath, dummyEmbeddings);
      LocalSearchClient.vectorstores.set(indexName, vectorstore);

      console.info(`Loaded FAISS index: ${indexName} from ${indexPath}`);
      return vectorstore;
    } finally {
      LocalSearchClient.loadingIndexes.delete(indexName);
    }
  }

  /**
   * Get vectorstore for a specific topic index.
   */
  async getVectorstore(indexName: IndexName): Promise<FaissStore> {
    return this.loadIndex(indexName);
  }

  /**
   * Search for documents in a specific topic index.
   */
  async search(indexName: IndexName, query: string, pageSize = 5): Promise<SearchResult[]> {
    const vectorstore = await this.getVectorstore(indexName);
    const settings = getSettings();

    // Search with similarity scores
    const docsWithScores = await vectorstore.similaritySearchWithScore(query, pageSize);

    return docsWithScores.map(([doc, score]) => {
      const metadata = (doc.metadata || {}) as Record<string, unknown>;
      const pdfName = String(metadata.title || metadata.source || 'Unknown');
      let sourceUrl = String(metadata.source_url || '');

      // Construct URL from base URL if not present
      if (!sourceUrl && settings.pdfBaseUrl) {
        const filename = String(metadata.filename || '');
        if (filename) {
          sourceUrl = `${settings.pdfBaseUrl}/${filename}`;
        }
      }

      const result: SearchResult = {
        content: doc.pageContent,
        pdfName,
        pdfUrl: sourceUrl,
        relevanceScore: score,
      };

      // Only set page if it's a valid number
      if (typeof metadata.page === 'number') {
        result.page = metadata.page;
      }

      return result;
    });
  }

  /**
   * Build context string from search results for RAG.
   */
  buildContext(results: SearchResult[]): string {
    if (results.length === 0) {
      return 'No relevant documents found.';
    }

    return results
      .map((result, i) => {
        let sourceInfo = `[Source ${i + 1}: ${result.pdfName}`;
        if (result.page) {
          sourceInfo += `, Page ${result.page}`;
        }
        sourceInfo += ']';
        return `${sourceInfo}\n${result.content}`;
      })
      .join('\n\n');
  }
}
