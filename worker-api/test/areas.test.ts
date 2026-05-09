import { describe, it, expect, beforeAll } from 'vitest';
import { SELF, env } from 'cloudflare:test';
import { seedDB } from './setup';

beforeAll(async () => {
  await seedDB(env.DB);
});

describe('GET /api/areas', () => {
  it('returns all seeded areas', async () => {
    const res = await SELF.fetch('http://localhost/api/areas');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(Array.isArray(json.data)).toBe(true);
    expect(json.data.length).toBe(3);
  });

  it('filters by q (area name substring)', async () => {
    const res = await SELF.fetch('http://localhost/api/areas?q=panther');
    const json = await res.json() as any;
    expect(json.data.length).toBeGreaterThanOrEqual(1);
    expect(json.data[0].area_name.toLowerCase()).toContain('panther');
  });

  it('filters by region (path prefix)', async () => {
    const res = await SELF.fetch('http://localhost/api/areas?region=arizona');
    const json = await res.json() as any;
    expect(json.data.every((a: any) => a.path.startsWith('/arizona/'))).toBe(true);
  });

  it('filters by parent_id', async () => {
    const res = await SELF.fetch('http://localhost/api/areas?parent_id=100');
    const json = await res.json() as any;
    expect(json.data.length).toBeGreaterThanOrEqual(1);
    expect(json.data.every((a: any) => a.parent_id === '100')).toBe(true);
  });
});

describe('GET /api/areas/:id/routes', () => {
  it('returns routes for area and descendants', async () => {
    // Area 300 (Panther Peak) has all 5 routes directly; area 100 (Arizona) is ancestor via path
    const res = await SELF.fetch('http://localhost/api/areas/300/routes');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(Array.isArray(json.data)).toBe(true);
    expect(json.data.length).toBeGreaterThanOrEqual(5);
    expect(json.area_id).toBe('300');
  });
});
