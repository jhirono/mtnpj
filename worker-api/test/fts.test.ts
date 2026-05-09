import { describe, it, expect, beforeAll } from 'vitest';
import { SELF, env } from 'cloudflare:test';
import { seedDB } from './setup';

beforeAll(async () => {
  await seedDB(env.DB);
});

describe('FTS5 full-text search', () => {
  it('returns routes matching "crack" in name or description', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?q=crack');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(Array.isArray(json.data)).toBe(true);
    expect(json.data.length).toBeGreaterThanOrEqual(1);
    // At least one result should mention "crack" in name or description
    const hasCrack = json.data.some((r: any) =>
      (r.route_name && r.route_name.toLowerCase().includes('crack')) ||
      (r.route_description && r.route_description.toLowerCase().includes('crack'))
    );
    expect(hasCrack).toBe(true);
  });

  it('returns empty data for nonexistent term', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?q=nonexistent_xyzzy_term');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(Array.isArray(json.data)).toBe(true);
    expect(json.data.length).toBe(0);
  });
});
