import { describe, it, expect, beforeAll, vi } from 'vitest';
import request from 'supertest';
import type { Express } from 'express';

// Mock the config to avoid needing real env vars in tests
vi.mock('../src/config.js', () => ({
  getSettings: () => ({
    environment: 'dev',
    gcpProjectId: 'test-project',
    gcpRegion: 'us-central1',
    geminiModel: 'gemini-2.5-flash',
    googleApiKey: 'test-key',
    faissIndexBasePath: './faiss_indexes',
    pdfBaseUrl: '',
    allowGeneralKnowledgeFallback: true,
    port: 8080,
  }),
  getValidatedSettings: () => ({
    environment: 'dev',
    gcpProjectId: 'test-project',
    gcpRegion: 'us-central1',
    geminiModel: 'gemini-2.5-flash',
    googleApiKey: 'test-key',
    faissIndexBasePath: './faiss_indexes',
    pdfBaseUrl: '',
    allowGeneralKnowledgeFallback: true,
    port: 8080,
  }),
  isDev: () => true,
  isProd: () => false,
  isWorkstation: () => false,
  usesServiceAccount: () => false,
  ConfigurationError: class ConfigurationError extends Error {
    constructor(public errors: string[]) {
      super(errors.join(', '));
    }
  },
}));

describe('API Endpoints', () => {
  let app: Express;

  beforeAll(async () => {
    const { createApp } = await import('../src/server.js');
    app = createApp();
  });

  describe('GET /health', () => {
    it('returns healthy status', async () => {
      const response = await request(app).get('/health');

      expect(response.status).toBe(200);
      expect(response.body).toEqual({ status: 'healthy' });
    });
  });

  describe('GET /', () => {
    it('returns API info', async () => {
      const response = await request(app).get('/');

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('name', 'Fund RAG Agent');
      expect(response.body).toHaveProperty('endpoints');
    });
  });
});

describe('Schema Validation', () => {
  it('validates ChatRequest schema', async () => {
    const { ChatRequestSchema } = await import('../src/types/schemas.js');

    const validRequest = { message: 'What is TFSA?' };
    expect(ChatRequestSchema.safeParse(validRequest).success).toBe(true);

    const invalidRequest = { message: '' };
    expect(ChatRequestSchema.safeParse(invalidRequest).success).toBe(false);

    const missingMessage = {};
    expect(ChatRequestSchema.safeParse(missingMessage).success).toBe(false);
  });
});
