import { serve } from '@hono/node-server';
import app, { logger } from './app.ts';

const port = Number(process.env.GENAI_PORT) || 3003;

if (process.env.NODE_ENV !== 'test') {
  serve(
    {
      fetch: app.fetch,
      hostname: '0.0.0.0',
      port: port,
    },
    (info) => {
      logger.info(`Server listening on http://${info.address}:${info.port}`);
    }
  );
}

export default app; 