import { z } from 'zod';
import { config } from 'dotenv';

config(); // Load .env file

const EnvironmentSchema = z.enum(['dev', 'prod', 'workstation']);

const SettingsSchema = z.object({
  environment: EnvironmentSchema.default('dev'),
  gcpProjectId: z.string().min(1, 'GCP_PROJECT_ID is required'),
  gcpRegion: z.string().default('us-central1'),
  geminiModel: z.string().default('gemini-2.5-flash'),
  googleApiKey: z.string().optional(),
  faissIndexBasePath: z.string().default('./faiss_indexes'),
  pdfBaseUrl: z.string().optional(),
  allowGeneralKnowledgeFallback: z
    .string()
    .transform((v) => v === 'true')
    .default('true'),
  port: z.coerce.number().default(8080),
});

export type Settings = z.infer<typeof SettingsSchema>;
export type Environment = z.infer<typeof EnvironmentSchema>;

let cachedSettings: Settings | null = null;

export function getSettings(): Settings {
  if (cachedSettings) return cachedSettings;

  const rawSettings = {
    environment: process.env.ENVIRONMENT,
    gcpProjectId: process.env.GCP_PROJECT_ID,
    gcpRegion: process.env.GCP_REGION,
    geminiModel: process.env.GEMINI_MODEL,
    googleApiKey: process.env.GOOGLE_API_KEY,
    faissIndexBasePath: process.env.FAISS_INDEX_BASE_PATH,
    pdfBaseUrl: process.env.PDF_BASE_URL,
    allowGeneralKnowledgeFallback: process.env.ALLOW_GENERAL_KNOWLEDGE_FALLBACK,
    port: process.env.PORT,
  };

  cachedSettings = SettingsSchema.parse(rawSettings);
  return cachedSettings;
}

export function getValidatedSettings(): Settings {
  const settings = getSettings();

  // Additional validation for dev environment
  if (settings.environment === 'dev' && !settings.googleApiKey) {
    throw new ConfigurationError([
      'GOOGLE_API_KEY is required for dev environment',
      'Use ENVIRONMENT=workstation for service account auth',
    ]);
  }

  return settings;
}

export class ConfigurationError extends Error {
  constructor(public errors: string[]) {
    const message = formatConfigError(errors);
    super(message);
    this.name = 'ConfigurationError';
  }
}

function formatConfigError(errors: string[]): string {
  return [
    '',
    '='.repeat(60),
    'CONFIGURATION ERROR',
    '='.repeat(60),
    '',
    'The following required settings are missing or invalid:',
    '',
    ...errors.map((e) => `  • ${e}`),
    '',
    'To fix this:',
    '  1. Copy .env.example to .env',
    '  2. Edit .env and add your configuration',
    '  3. Restart the application',
    '='.repeat(60),
  ].join('\n');
}

// Helper methods
export function isDev(settings: Settings): boolean {
  return settings.environment === 'dev';
}

export function isProd(settings: Settings): boolean {
  return settings.environment === 'prod';
}

export function isWorkstation(settings: Settings): boolean {
  return settings.environment === 'workstation';
}

export function usesServiceAccount(settings: Settings): boolean {
  return settings.environment === 'prod' || settings.environment === 'workstation';
}
