import { createRoute, OpenAPIHono } from '@hono/zod-openapi';
import { Scalar } from '@scalar/hono-api-reference'
import dotenv from 'dotenv';
import pino from 'pino';
import { z } from 'zod';
import { ChatOpenAI } from '@langchain/openai';
import { HumanMessage } from '@langchain/core/messages';
import { cors } from 'hono/cors';

dotenv.config();

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  ...(process.env.NODE_ENV !== 'production' && { transport: { target: 'pino-pretty', options: { colorize: true } } }),
});

const app = new OpenAPIHono();

app.use(cors());

app.openapi(createRoute(
  {
    method: 'get',
    path: '/health',
    responses: {
      200: {
        description: 'Responds with a 200 status if the service is healthy.',
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                status: { type: 'string', example: 'ok' },  
              },
            },
          },
        },
      },
    },  
  }),
  (c) => {
    return c.json({ status: 'ok' });
  }
);

// OpenAPI UI
app.get('/scalar', Scalar({ url: '/doc' }))

// OpenAPI JSON spec
app.doc('/doc', {
  openapi: '3.1.0',
  info: {
    version: '1.0.0',
    title: 'LangChain AI Service API',
    description: 'API for interacting with the LangChain AI service.',
  },
  servers: [
    {
      url: `http://localhost:${process.env.GENAI_PORT || 3003}`,
      description: 'Development server',
    },
  ],
});

const PredictRequestSchema = z.object({
  input: z.string().openapi({
    example: 'What is the capital of France?',
    description: 'The input text for the LangChain model',
  }),
});

const PredictResponseSchema = z.object({
  output: z.string().openapi({
    example: 'The capital of France is Paris.',
    description: 'The output from the LangChain model',
  }),
});

// Predict endpoint
 app.openapi(
  createRoute({
    method: 'post',
    path: '/predict',
    request: {
      body: {
        content: {
          'application/json': {
            schema: PredictRequestSchema,
          },
        },
      },
    },
    responses: {
      200: {
        description: 'Successful response from the LangChain model.',
        content: {
          'application/json': {
            schema: PredictResponseSchema,
          },
        },
      },
      400: {
        description: 'Invalid input.',
      },
      500: {
        description: 'Error processing the request.',
      },
    },
    tags: ['AI'],
  }),
  async (c) => {
    const { input } = c.req.valid('json');
    logger.info({ input }, 'Predict request received');

    try {
      if (!process.env.OPENAI_API_KEY) {
        logger.error('OPENAI_API_KEY is not set.');
        return c.json({ error: 'OpenAI API key not configured.' }, 500);
      }

      const model = new ChatOpenAI({
        apiKey: process.env.OPENAI_API_KEY,
        modelName: process.env.LANGCHAIN_MODEL_NAME || 'gpt-3.5-turbo',
      });

      const message = new HumanMessage({ content: input });
      const result = await model.invoke([message]);
      
      const output = result.content.toString();
      logger.info({ output }, 'Prediction successful');
      return c.json({ output });
    } catch (error: unknown) {
      logger.error({ err: error }, 'Error during prediction');
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
      return c.json({ error: 'Failed to get prediction from LangChain model', details: errorMessage }, 500);
    }
  }
);

export default app;