import express, { type Request, type Response, type NextFunction } from 'express';
import cors from 'cors';
import { ChatRequestSchema, type ChatResponse } from './types/schemas.js';
import { Orchestrator } from './orchestrator/index.js';
import { getSettings, isDev } from './config.js';
import { formatErrorResponse } from './utils/responses.js';

export function createApp() {
  const app = express();

  // Middleware
  app.use(cors());
  app.use(express.json());

  // Lazy-initialized orchestrator (singleton pattern)
  let orchestrator: Orchestrator | null = null;

  function getOrchestrator(): Orchestrator {
    if (!orchestrator) {
      orchestrator = new Orchestrator();
    }
    return orchestrator;
  }

  // Health check
  app.get('/health', (_req: Request, res: Response) => {
    res.json({ status: 'healthy' });
  });

  // Root endpoint
  app.get('/', (_req: Request, res: Response) => {
    res.json({
      name: 'Fund RAG Agent',
      version: '0.1.0',
      endpoints: {
        '/chat': 'POST - Send a message and get a response',
        '/health': 'GET - Health check',
      },
    });
  });

  // Chat endpoint
  app.post('/chat', async (req: Request, res: Response, next: NextFunction) => {
    try {
      // Validate request body
      const parseResult = ChatRequestSchema.safeParse(req.body);
      if (!parseResult.success) {
        res.status(400).json({ error: 'Message cannot be empty' });
        return;
      }

      const { message } = parseResult.data;
      const settings = getSettings();

      try {
        const orch = getOrchestrator();
        const response: ChatResponse = await orch.process(message);
        res.json(response);
      } catch (error) {
        if (isDev(settings)) {
          console.error('Error processing chat:', error);
          res.status(500).json({
            error: error instanceof Error ? error.message : 'Unknown error',
          });
          return;
        }
        res.json(formatErrorResponse('An unexpected error occurred'));
      }
    } catch (error) {
      next(error);
    }
  });

  // Error handler
  app.use((err: Error, _req: Request, res: Response, _next: NextFunction) => {
    console.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
  });

  return app;
}
