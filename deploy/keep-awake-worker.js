/**
 * Keeps the blog from being stopped for being idle.
 *
 * Render stops a free web service after 15 minutes with no requests, and
 * starting it again takes around 36 seconds — measured, not guessed — which
 * the unlucky visitor spends looking at a blank tab. A request every five
 * minutes means it is never idle long enough to be stopped.
 *
 * It also keeps the database awake. Neon's free plan suspends a compute after
 * five minutes and that cannot be turned off, so the first query after a quiet
 * spell pays several hundred milliseconds to wake it. Loading the homepage
 * runs a query, so the same ping covers both.
 *
 * This is deliberately a Cloudflare Worker rather than GitHub Actions. The
 * same job on Actions ran 12 times in three days instead of 170, with an
 * average gap of five hours — every gap long enough for the site to sleep.
 * Cloudflare's cron triggers run on time.
 *
 * Deploy: Cloudflare dashboard → Workers & Pages → Create → paste this →
 * Settings → Triggers → Cron Triggers → add "*\/5 * * * *".
 */

const SITE = "https://blog.sureshsurkheti.com/";

export default {
  async scheduled(event, env, ctx) {
    // A unique query string on every request. Nothing caches the homepage
    // today, but a cached reply would be served by Cloudflare without ever
    // reaching Render — the ping would look fine and wake nothing.
    const url = `${SITE}?keepalive=${Date.now()}`;

    const response = await fetch(url, {
      headers: { "User-Agent": "keep-awake-worker" },
      cf: { cacheTtl: 0, cacheEverything: false },
    });

    // Shows up in `wrangler tail` and the Worker's logs.
    console.log(`keep-awake -> HTTP ${response.status}`);
  },

  // Visiting the Worker's own URL reports what it is, so it is not a mystery
  // in the dashboard in six months' time.
  async fetch() {
    return new Response(
      "Keep-alive worker for blog.sureshsurkheti.com — runs every 5 minutes.\n",
      { headers: { "content-type": "text/plain" } },
    );
  },
};
