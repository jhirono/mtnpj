import { defineWorkersConfig } from '@cloudflare/vitest-pool-workers/config';

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        miniflare: {
          d1Databases: ['DB'],
        },
        wrangler: { configPath: './wrangler.toml' },
      },
    },
  },
});
