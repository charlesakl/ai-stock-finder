# AI response caching

Six-agent model responses and investment committee responses are saved to `.ai_cache/` in the project folder and reused for 24 hours **only when the model, instructions, and substantive input data match**. Changes to stock price, quality checks, SEC facts, evidence or investment horizon invalidate affected entries. Model responses that fail are not cached. The API key is never written to the cache.

The app still fetches market data and non-AI evidence; only paid AI responses are cached. Because news and fundamentals can change, do not treat cached responses as live market signals. Cache files are ignored by Git. Delete `.ai_cache` to force fresh model calls, or set `AI_CACHE_HOURS=0` in `.env` to disable caching. For a different duration, set e.g. `AI_CACHE_HOURS=12`.

Cache keys omit retrieval-only timestamps to allow re-use for unchanged substantive data. Six-agent reviews that stopped halfway can resume using already-cached specialist results. Cache is per machine/project folder.
