import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import app from '../src/app.ts';

describe('API Endpoints', () => {

  before(() => {
    // Nothing to set up before tests for now,
  });

  after(() => {
    // Clean up resources if any
  });

  describe('/health endpoint', () => {
    it('should return 200 OK with status: ok', async () => {
      const res = await app.request('/health');
      assert.strictEqual(res.status, 200);
      const body = await res.json();
      assert.deepStrictEqual(body, { status: 'ok' });
    });
  });
}); 