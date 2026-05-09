import { describe, it, expect, beforeAll } from 'vitest';
import { SELF, env } from 'cloudflare:test';
import { seedDB } from './setup';

beforeAll(async () => {
  await seedDB(env.DB);
});

describe('GET /api/routes', () => {
  it('returns paginated list', async () => {
    const res = await SELF.fetch('http://localhost/api/routes');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(Array.isArray(json.data)).toBe(true);
    expect(json.data.length).toBe(5);
    expect(json.page).toBe(1);
    expect(json.limit).toBe(50);
  });

  it('filters by type=sport', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?type=sport');
    const json = await res.json() as any;
    expect(json.data.every((r: any) => r.is_sport === 1)).toBe(true);
  });

  it('returns aid routes when type=aid (D-01: aid coverage)', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?type=aid');
    const json = await res.json() as any;
    expect(json.data.length).toBeGreaterThanOrEqual(1);
    expect(json.data[0].is_aid).toBe(1);
  });

  it('rejects invalid type with 400', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?type=invalid');
    expect(res.status).toBe(400);
  });

  it('blocks SQL injection attempt on type param', async () => {
    const malicious = encodeURIComponent("sport;DROP TABLE routes;--");
    const res = await SELF.fetch(`http://localhost/api/routes?type=${malicious}`);
    expect(res.status).toBe(400);
    // Verify routes table still has rows
    const probe = await SELF.fetch('http://localhost/api/routes');
    expect(probe.status).toBe(200);
    const probeJson = await probe.json() as any;
    expect(probeJson.data.length).toBe(5);
  });

  it('filters by stars_min', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?stars_min=3.6');
    const json = await res.json() as any;
    expect(json.data.every((r: any) => r.route_stars >= 3.6)).toBe(true);
  });

  it('filters by exact grade', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade=5.10b');
    const json = await res.json() as any;
    expect(json.data.every((r: any) => r.route_grade === '5.10b')).toBe(true);
  });

  it('filters by numeric grade range', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?grade_min=9&grade_max=11');
    const json = await res.json() as any;
    expect(json.data.every((r: any) => r.route_grade_numeric >= 9 && r.route_grade_numeric <= 11)).toBe(true);
  });

  it('filters by region (path prefix)', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?region=arizona');
    const json = await res.json() as any;
    expect(json.data.every((r: any) => r.area_path.startsWith('/arizona/'))).toBe(true);
  });

  it('paginates correctly', async () => {
    const res1 = await SELF.fetch('http://localhost/api/routes?page=1&limit=2');
    const res2 = await SELF.fetch('http://localhost/api/routes?page=2&limit=2');
    const j1 = await res1.json() as any;
    const j2 = await res2.json() as any;
    expect(j1.data.length).toBe(2);
    expect(j2.data.length).toBe(2);
    expect(j1.data[0].route_id).not.toBe(j2.data[0].route_id);
  });

  it('rejects limit > 200', async () => {
    const res = await SELF.fetch('http://localhost/api/routes?limit=999');
    expect(res.status).toBe(400);
  });
});

describe('GET /api/routes/:id', () => {
  it('returns route by id', async () => {
    const res = await SELF.fetch('http://localhost/api/routes/12345');
    expect(res.status).toBe(200);
    const json = await res.json() as any;
    expect(json.data.route_name).toBe('The Nose');
  });

  it('returns 404 for unknown id', async () => {
    const res = await SELF.fetch('http://localhost/api/routes/nonexistent_999');
    expect(res.status).toBe(404);
  });
});
