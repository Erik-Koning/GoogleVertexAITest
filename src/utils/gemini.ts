import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { ChatVertexAI } from '@langchain/google-vertexai';
import { GoogleGenerativeAI } from '@google/generative-ai';
import type { BaseChatModel } from '@langchain/core/language_models/chat_models';
import { HumanMessage, SystemMessage } from '@langchain/core/messages';
import { getSettings, isDev } from '../config.js';

/**
 * Returns LangChain LLM based on environment.
 * - Dev: Uses API key via @langchain/google-genai
 * - Prod/Workstation: Uses Vertex AI via @langchain/google-vertexai
 */
export function getLLM(): BaseChatModel {
  const settings = getSettings();

  if (isDev(settings)) {
    if (!settings.googleApiKey) {
      throw new Error('GOOGLE_API_KEY is required for dev environment');
    }
    return new ChatGoogleGenerativeAI({
      model: settings.geminiModel,
      apiKey: settings.googleApiKey,
    });
  }

  // Prod and Workstation use service account via ADC
  return new ChatVertexAI({
    model: settings.geminiModel,
    // @ts-expect-error - project/location are valid for VertexAI but types may not reflect it
    project: settings.gcpProjectId,
    location: settings.gcpRegion,
  });
}

// Cached client instances
let genAIClient: GoogleGenerativeAI | null = null;

/**
 * Get the GoogleGenerativeAI client for direct API calls.
 * Used for structured output (chart data extraction).
 */
function getGenAIClient(): GoogleGenerativeAI {
  if (!genAIClient) {
    const settings = getSettings();

    if (isDev(settings)) {
      if (!settings.googleApiKey) {
        throw new Error('GOOGLE_API_KEY is required for dev environment');
      }
      genAIClient = new GoogleGenerativeAI(settings.googleApiKey);
    } else {
      // For Vertex AI, we need to use the langchain client differently
      // The @google/generative-ai package doesn't support Vertex AI directly
      // We'll use a workaround by calling the LangChain LLM
      throw new Error('Direct Gemini client not available in prod/workstation - use LangChain LLM');
    }
  }
  return genAIClient;
}

/**
 * Generate text content using Gemini.
 */
export async function generateContent(
  prompt: string,
  systemInstruction?: string
): Promise<string> {
  const settings = getSettings();

  if (isDev(settings)) {
    const client = getGenAIClient();
    const modelConfig: Parameters<typeof client.getGenerativeModel>[0] = {
      model: settings.geminiModel,
    };
    if (systemInstruction) {
      modelConfig.systemInstruction = systemInstruction;
    }
    const model = client.getGenerativeModel(modelConfig);
    const result = await model.generateContent(prompt);
    return result.response.text();
  }

  // For prod/workstation, use LangChain
  const llm = getLLM();
  const messages = [];

  if (systemInstruction) {
    messages.push(new SystemMessage(systemInstruction));
  }
  messages.push(new HumanMessage(prompt));

  const response = await llm.invoke(messages);
  return typeof response.content === 'string' ? response.content : JSON.stringify(response.content);
}

/**
 * Generate structured output using Gemini.
 * Used for chart data extraction with JSON schema.
 */
export async function generateStructured<T>(
  prompt: string,
  responseSchema: object,
  systemInstruction?: string
): Promise<T> {
  const settings = getSettings();

  if (isDev(settings)) {
    const client = getGenAIClient();
    const modelConfig: Parameters<typeof client.getGenerativeModel>[0] = {
      model: settings.geminiModel,
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: responseSchema as Parameters<
          typeof client.getGenerativeModel
        >[0]['generationConfig'] extends { responseSchema?: infer S } ? S : never,
      },
    };
    if (systemInstruction) {
      modelConfig.systemInstruction = systemInstruction;
    }
    const model = client.getGenerativeModel(modelConfig);
    const result = await model.generateContent(prompt);
    return JSON.parse(result.response.text()) as T;
  }

  // For prod/workstation, use LangChain with structured output
  const llm = getLLM();

  // Create a prompt that requests JSON output
  const jsonPrompt = `${systemInstruction ? systemInstruction + '\n\n' : ''}${prompt}

IMPORTANT: Respond with valid JSON only, following this schema:
${JSON.stringify(responseSchema, null, 2)}`;

  const response = await llm.invoke([new HumanMessage(jsonPrompt)]);
  const content = typeof response.content === 'string' ? response.content : '';

  // Extract JSON from response (handle markdown code blocks)
  const jsonMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/) || [null, content];
  const jsonStr = jsonMatch[1]?.trim() || content.trim();

  return JSON.parse(jsonStr) as T;
}
