import { createApp } from './server.js';
import { getValidatedSettings, ConfigurationError } from './config.js';

async function main() {
  console.info('Starting Fund RAG Agent...');

  // Validate configuration
  let settings;
  try {
    settings = getValidatedSettings();
  } catch (error) {
    if (error instanceof ConfigurationError) {
      console.error(error.message);
      process.exit(1);
    }
    throw error;
  }

  const app = createApp();

  app.listen(settings.port, () => {
    console.info(`Fund RAG Agent ready on port ${settings.port}`);
    console.info(`Environment: ${settings.environment}`);
    console.info(`FAISS Indexes: ${settings.faissIndexBasePath}`);
    console.info(`Gemini Model: ${settings.geminiModel}`);
  });
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
