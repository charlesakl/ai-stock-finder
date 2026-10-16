# AI usage limits (Phase 11)

- Free Research: unlimited OpenAI-free screening (external market-data rate limits still apply).
- AI Research: 5 manually requested workflows per UTC day.
- Advanced AI Research: 2 manually requested workflows per UTC day, including committee comparisons.
- Global paid workflow cap: 20 per UTC day.

## Important deployment restrictions

**Paid AI is OFF by default.** To enable it for your private, local computer, add `ENABLE_PAID_AI=true` to `.env` (never commit that file). Set `LOCAL_USER_ID` if needed. The counter is stored in `.usage_limits.sqlite3` in the application directory, and that file is ignored by Git.

This version is suitable for **one trusted local user**. It does **not** enforce separate quotas for anonymous internet visitors: every visitor would share a single `LOCAL_USER_ID`. Do not enable paid AI on a public Streamlit deployment. Public per-user quotas require verified sign-in and a shared durable database with atomic reservations, e.g. managed PostgreSQL; local SQLite storage may reset on cloud redeploy/restart. The global cap is a request count, **not a hard dollar limit**. A six-agent workflow can make multiple billable model calls. Keep OpenAI billing alerts and limits configured separately.

Quota slots are reserved before starting paid workflows and are not refunded automatically on failures or cache hits. This conservative policy avoids bypassing limits. Usage resets at midnight UTC. A separate cache reduces repeated API cost but does not guarantee no charge.
