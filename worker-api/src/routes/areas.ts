import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';
import type { Bindings, AreaRow, RouteRow } from '../types';
import { buildAreasQuery, buildRoutesQuery } from '../db/queries';

const app = new Hono<{ Bindings: Bindings }>();

const areaQuerySchema = z.object({
  q: z.string().min(1).optional(),
  region: z.string().regex(/^[a-z0-9-]+$/).optional(),
  parent_id: z.string().optional(),
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(50),
});

app.get('/areas', zValidator('query', areaQuerySchema), async (c) => {
  const f = c.req.valid('query');
  const { sql, params } = buildAreasQuery(f);
  const { results } = await c.env.DB.prepare(sql).bind(...params).all<AreaRow>();
  return c.json({ data: results ?? [], page: f.page, limit: f.limit });
});

const areaRoutesQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(50),
});

app.get('/areas/:id/routes', zValidator('query', areaRoutesQuerySchema), async (c) => {
  const id = c.req.param('id');
  const f = c.req.valid('query');
  const { sql, params } = buildRoutesQuery({ area_id: id, page: f.page, limit: f.limit });
  const { results } = await c.env.DB.prepare(sql).bind(...params).all<RouteRow & { area_path: string; area_name: string }>();
  return c.json({ data: results ?? [], page: f.page, limit: f.limit, area_id: id });
});

export default app;
