import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import type { Bindings, RouteRow } from '../types';
import { ALLOWED_TYPES } from '../types';
import { buildRoutesQuery } from '../db/queries';

const app = new Hono<{ Bindings: Bindings }>();

const routeQuerySchema = z.object({
  q: z.string().min(1).optional(),
  grade: z.string().optional(),
  grade_min: z.coerce.number().optional(),
  grade_max: z.coerce.number().optional(),
  type: z.enum(ALLOWED_TYPES).optional(),
  region: z.string().regex(/^[a-z0-9-]+$/, 'region must be slug').optional(),
  stars_min: z.coerce.number().min(0).max(4).optional(),
  votes_min: z.coerce.number().min(0).optional(),
  area_id: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(50),
});

app.get('/routes', zValidator('query', routeQuerySchema), async (c) => {
  const f = c.req.valid('query');

  // Resolve area_path before building the query so we avoid a subquery inside LIKE,
  // which D1 does not support ("LIKE or GLOB pattern too complex").
  let resolvedAreaPath: string | undefined;
  if (f.area_id) {
    const areaRow = await c.env.DB
      .prepare('SELECT path FROM areas WHERE area_id = ? LIMIT 1')
      .bind(f.area_id)
      .first<{ path: string }>();
    resolvedAreaPath = areaRow?.path;
  }

  const { sql, params } = buildRoutesQuery({ ...f, area_path: resolvedAreaPath });
  const { results } = await c.env.DB.prepare(sql).bind(...params).all<RouteRow & { area_path: string; area_name: string; area_url: string | null }>();
  return c.json({ data: results ?? [], page: f.page, limit: f.limit });
});

app.get('/routes/:id', async (c) => {
  const id = c.req.param('id');
  const row = await c.env.DB
    .prepare('SELECT r.*, a.path AS area_path, a.area_name, a.area_url FROM routes r JOIN areas a ON r.area_id = a.area_id WHERE r.route_id = ? LIMIT 1')
    .bind(id)
    .first<RouteRow & { area_path: string; area_name: string; area_url: string | null }>();
  if (!row) return c.json({ error: 'route not found' }, 404);
  return c.json({ data: row });
});

export default app;
