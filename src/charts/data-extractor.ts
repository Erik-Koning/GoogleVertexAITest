import { generateStructured } from '../utils/gemini.js';
import type { ChartType } from '../types/schemas.js';

const EXTRACTION_SYSTEM_PROMPT = `You are a data extraction assistant. Your job is to extract numerical data from the provided context that can be used to create a chart.

Rules:
1. Only extract data that is explicitly mentioned in the context
2. Do not make up or estimate values
3. Use appropriate labels from the context
4. If no suitable data exists for a chart, set has_data to false
5. Round percentages to 1 decimal place
6. Ensure all values are numbers (not strings)`;

interface ChartDataResult {
  data: Record<string, number>;
  title: string;
  has_data: boolean;
}

const RESPONSE_SCHEMA = {
  type: 'object',
  properties: {
    data: {
      type: 'object',
      description: 'Key-value pairs where keys are labels and values are numbers',
      additionalProperties: { type: 'number' },
    },
    title: {
      type: 'string',
      description: 'A descriptive title for the chart',
    },
    has_data: {
      type: 'boolean',
      description: 'Whether suitable data was found in the context',
    },
  },
  required: ['data', 'title', 'has_data'],
};

/**
 * Extract chart data from context using Gemini structured output.
 */
export async function extractChartData(
  userQuery: string,
  context: string,
  chartType: ChartType
): Promise<{ data: Record<string, number>; title: string } | null> {
  const prompt = `Based on the user's question and the context provided, extract data suitable for a ${chartType} chart.

User Question: ${userQuery}

Context:
${context}

Extract the relevant numerical data and provide an appropriate chart title. If no suitable numerical data exists, set has_data to false.`;

  try {
    const result = await generateStructured<ChartDataResult>(
      prompt,
      RESPONSE_SCHEMA,
      EXTRACTION_SYSTEM_PROMPT
    );

    if (!result.has_data || !result.data || Object.keys(result.data).length === 0) {
      return null;
    }

    return {
      data: result.data,
      title: result.title,
    };
  } catch (error) {
    console.warn(`Chart data extraction failed: ${error}`);
    return null;
  }
}
