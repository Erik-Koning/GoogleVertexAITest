import { StructuredOutputParser } from 'langchain/output_parsers';
import { ChatPromptTemplate } from '@langchain/core/prompts';
import { RunnableSequence } from '@langchain/core/runnables';
import { z } from 'zod';
import { getLLM } from '../utils/gemini.js';
import { TFSATool } from '../tools/tfsa-tool.js';
import { RRSPTool } from '../tools/rrsp-tool.js';
import { FundFactsTool } from '../tools/fund-facts-tool.js';
import { ROUTING_SYSTEM_PROMPT, ROUTING_USER_PROMPT } from './prompts.js';
import type { BaseTool } from '../tools/base.js';
import type { ChatResponse, OrchestratorDecision, ToolType, ChartType } from '../types/schemas.js';
import { toApiResponse } from '../types/schemas.js';

// Router output schema for LangChain structured parsing
const RouterOutputSchema = z.object({
  tool: z.enum(['tfsa', 'rrsp', 'fund_facts']),
  generate_chart: z.boolean(),
  chart_type: z.enum(['bar', 'line', 'pie', 'scatter', 'histogram']),
  reasoning: z.string(),
});

type RouterOutput = z.infer<typeof RouterOutputSchema>;

export class Orchestrator {
  private tools: Map<ToolType, BaseTool>;
  private llm;
  private parser;
  private prompt;
  private chain;

  constructor() {
    this.tools = new Map<ToolType, BaseTool>([
      ['tfsa', new TFSATool()],
      ['rrsp', new RRSPTool()],
      ['fund_facts', new FundFactsTool()],
    ]);

    this.llm = getLLM();
    this.parser = StructuredOutputParser.fromZodSchema(RouterOutputSchema);

    this.prompt = ChatPromptTemplate.fromMessages([
      ['system', `${ROUTING_SYSTEM_PROMPT}\n\n{format_instructions}`],
      ['human', ROUTING_USER_PROMPT],
    ]);

    // Build the routing chain: prompt -> llm -> parser
    this.chain = RunnableSequence.from([this.prompt, this.llm, this.parser]);
  }

  /**
   * Determine which tool should handle the query and chart parameters.
   */
  async route(userQuery: string): Promise<OrchestratorDecision> {
    try {
      const result = (await this.chain.invoke({
        user_query: userQuery,
        format_instructions: this.parser.getFormatInstructions(),
      })) as RouterOutput;

      return {
        tool: result.tool,
        userQuery,
        generateChart: result.generate_chart,
        chartType: result.chart_type as ChartType,
        reasoning: result.reasoning,
      };
    } catch (error) {
      // If routing fails, default to fund_facts without chart
      console.warn(`Routing failed, defaulting to fund_facts: ${error}`);
      return {
        tool: 'fund_facts',
        userQuery,
        generateChart: false,
        chartType: 'bar',
        reasoning: 'Routing failed, using default',
      };
    }
  }

  /**
   * Process a user query end-to-end.
   */
  async process(userQuery: string): Promise<ChatResponse> {
    // 1. Route the query
    const decision = await this.route(userQuery);

    // 2. Get the appropriate tool
    const tool = this.tools.get(decision.tool) ?? this.tools.get('fund_facts')!;

    // 3. Invoke the tool
    const toolResponse = await tool.invoke({
      userQuery: decision.userQuery,
      generateChart: decision.generateChart,
      chartType: decision.chartType,
    });

    // 4. Return as ChatResponse (convert to snake_case for API)
    return toApiResponse(toolResponse);
  }
}
