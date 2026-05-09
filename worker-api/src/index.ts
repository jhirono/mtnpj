import { Hono } from 'hono';
import { cors } from 'hono/cors';
import type { Bindings } from './types';
import routesRouter from './routes/routes';
import areasRouter from './routes/areas';

const app = new Hono<{ Bindings: Bindings }>();

// CORS must be registered BEFORE routes (RESEARCH.md Pitfall 5)
app.use('/api/*', cors({
  origin: (origin) => {
    if (!origin) return '*';
    if (origin === 'http://localhost:5173') return origin;
    if (origin.endsWith('.pages.dev')) return origin;
    return undefined; // block other origins
  },
  allowMethods: ['GET', 'OPTIONS'],
  maxAge: 86400,
}));

app.get('/api/health', (c) => c.json({ ok: true }));
app.route('/api', routesRouter);
app.route('/api', areasRouter);

app.notFound((c) => c.json({ error: 'not found' }, 404));
app.onError((err, c) => {
  console.error('Unhandled:', err);
  return c.json({ error: 'internal error' }, 500);
});

export default app;
