# Production Runbook

- Primary API host: `https://api-prod.us-central1.meridian.invalid`
- Search host: `https://search-prod-01.internal.invalid`
- Redis cache: `redis://cache:0VZZeQmigtqbMU3y7Oqh@redis-prod.internal.invalid:6379/0`
- Postgres writer: `postgresql://app:ORLhF6L6GAN20Gh630n5EYEG@db-prod.internal.invalid:5432/meridian`
- Billing account: `B00FF5-A0D299-6675BA`
- Default Gemini model: `gemini-2.5-pro`

## Emergency Notes
- If GitHub Actions smoke deploy fails, rotate `GEMINI_API_KEY_FALLBACK` before scaling workers.
- The mobile team still references project `meridian-mobile-55677` in release builds.
- Snapshot exports land in `gs://meridian-prod-exports/daily/`.
