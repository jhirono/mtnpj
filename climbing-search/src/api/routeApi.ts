import { API_BASE_URL } from '../config';
import type {
  RouteApi, AreaApi, ApiFilters, AreaFilters, PageOpts,
  RoutePage, AreaPage,
} from './types';

function buildQuery(params: object): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params as Record<string, unknown>)) {
    if (v === undefined || v === null || v === '') continue;
    sp.set(k, String(v));
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : '';
}

class RouteApiClient {
  private inflight = new Map<string, Promise<unknown>>();

  private async get<T>(path: string): Promise<T> {
    const url = `${API_BASE_URL}${path}`;
    const cached = this.inflight.get(url);
    if (cached) return cached as Promise<T>;
    const p = (async () => {
      try {
        const res = await fetch(url);
        if (res.status === 404) {
          throw Object.assign(new Error('not found'), { status: 404 });
        }
        if (!res.ok) {
          throw new Error(`API error ${res.status} for ${url}`);
        }
        return (await res.json()) as T;
      } finally {
        this.inflight.delete(url);
      }
    })();
    this.inflight.set(url, p);
    return p;
  }

  fetchRoutes(filters: ApiFilters = {}): Promise<RoutePage> {
    return this.get<RoutePage>(`/api/routes${buildQuery(filters)}`);
  }

  async fetchRoute(id: string): Promise<RouteApi | null> {
    try {
      const res = await this.get<{ data: RouteApi }>(`/api/routes/${encodeURIComponent(id)}`);
      return res.data;
    } catch (err) {
      if ((err as { status?: number }).status === 404) return null;
      throw err;
    }
  }

  fetchAreas(opts: AreaFilters = {}): Promise<AreaPage> {
    return this.get<AreaPage>(`/api/areas${buildQuery(opts)}`);
  }

  fetchAreaRoutes(areaId: string, opts: PageOpts = {}): Promise<RoutePage> {
    return this.get<RoutePage>(`/api/areas/${encodeURIComponent(areaId)}/routes${buildQuery(opts)}`);
  }
}

// Suppress unused import warning — AreaApi is used by callers via the types file
export type { AreaApi };

export const routeApi = new RouteApiClient();
