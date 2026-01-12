import { z } from 'zod';

// Chart type literal
export const ChartTypeSchema = z.enum(['bar', 'line', 'pie', 'scatter', 'histogram']);
export type ChartType = z.infer<typeof ChartTypeSchema>;

// Tool type literal
export const ToolTypeSchema = z.enum(['tfsa', 'rrsp', 'fund_facts']);
export type ToolType = z.infer<typeof ToolTypeSchema>;

// Source document reference
export const SourceSchema = z.object({
  pdfName: z.string(),
  pdfUrl: z.string(),
  page: z.number().optional(),
  snippet: z.string().optional(),
});
export type Source = z.infer<typeof SourceSchema>;

// Tool input
export const ToolInputSchema = z.object({
  userQuery: z.string(),
  generateChart: z.boolean().default(false),
  chartType: ChartTypeSchema.default('bar'),
});
export type ToolInput = z.infer<typeof ToolInputSchema>;

// Response metadata
export const ResponseMetadataSchema = z.object({
  searchResultsCount: z.number().default(0),
  dataStoreEmpty: z.boolean().default(false),
  usedInternalKnowledge: z.boolean().default(false),
  indexUsed: z.string().optional(),
  warning: z.string().optional(),
});
export type ResponseMetadata = z.infer<typeof ResponseMetadataSchema>;

// Tool response (internal)
export const ToolResponseSchema = z.object({
  reply: z.string(),
  chartType: z.string().optional(),
  imageBase64: z.string().optional(),
  sources: z.array(SourceSchema).default([]),
  metadata: ResponseMetadataSchema.optional(),
});
export type ToolResponse = z.infer<typeof ToolResponseSchema>;

// Chat request (API input)
export const ChatRequestSchema = z.object({
  message: z.string().min(1, 'Message cannot be empty'),
});
export type ChatRequest = z.infer<typeof ChatRequestSchema>;

// Chat response (API output) - uses snake_case for API compatibility with Python version
export const ChatResponseSchema = z.object({
  reply: z.string(),
  chart_type: z.string().optional(),
  image_base64: z.string().optional(),
  sources: z
    .array(
      z.object({
        pdf_name: z.string(),
        pdf_url: z.string(),
        page: z.number().optional(),
        snippet: z.string().optional(),
      })
    )
    .default([]),
  metadata: z
    .object({
      search_results_count: z.number().optional(),
      data_store_empty: z.boolean().optional(),
      used_internal_knowledge: z.boolean().optional(),
      index_used: z.string().optional(),
      warning: z.string().optional(),
    })
    .optional(),
});
export type ChatResponse = z.infer<typeof ChatResponseSchema>;

// Orchestrator decision
export const OrchestratorDecisionSchema = z.object({
  tool: ToolTypeSchema,
  userQuery: z.string(),
  generateChart: z.boolean().default(false),
  chartType: ChartTypeSchema.default('bar'),
  reasoning: z.string(),
});
export type OrchestratorDecision = z.infer<typeof OrchestratorDecisionSchema>;

// Router output (LangChain structured output)
export const RouterOutputSchema = z.object({
  tool: ToolTypeSchema,
  generate_chart: z.boolean().default(false),
  chart_type: ChartTypeSchema.default('bar'),
  reasoning: z.string(),
});
export type RouterOutput = z.infer<typeof RouterOutputSchema>;

// Helper function to convert internal ToolResponse to API ChatResponse
export function toApiResponse(response: ToolResponse): ChatResponse {
  return {
    reply: response.reply,
    chart_type: response.chartType,
    image_base64: response.imageBase64,
    sources: response.sources.map((s) => ({
      pdf_name: s.pdfName,
      pdf_url: s.pdfUrl,
      page: s.page,
      snippet: s.snippet,
    })),
    metadata: response.metadata
      ? {
          search_results_count: response.metadata.searchResultsCount,
          data_store_empty: response.metadata.dataStoreEmpty,
          used_internal_knowledge: response.metadata.usedInternalKnowledge,
          index_used: response.metadata.indexUsed,
          warning: response.metadata.warning,
        }
      : undefined,
  };
}
