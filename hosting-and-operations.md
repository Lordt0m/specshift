# Zero-cost hosting and operations

Hosting target, checked against first-party docs on 9 October 2026: static Vite build on Cloudflare Pages Free; stateless Django API on Render Free web service. These free plans are changeable and availability is not guaranteed. The application must also remain runnable locally without either provider.

## Preflight before creating resources

1. Recheck current [Cloudflare Pages React guide](https://developers.cloudflare.com/pages/framework-guides/deploy-a-react-site/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/) and [Render Free terms](https://render.com/docs/free/). Confirm both accounts permit the exact project without a required payment method and that no existing account usage would incur charges.
2. Obtain Ayotomiwa's approval for remote repo, accounts and public URLs. He may need to sign in, accept terms and control credentials. Keep secrets out of chat, repository and browser bundle.
3. Confirm the Render service is configured as Free, one web service only, with no persistent disk, cron, worker, paid database or billable add-on. Confirm Cloudflare is Pages Free, not a Workers paid setup.

## Deployment sequence

Create source repository only after authorization. Keep the API and web in the monorepo. Deploy API first: production Django settings, pinned requirements, Gunicorn or equivalent WSGI server, host-provided port, bounded worker count/timeouts, health endpoint and `DEBUG=False`. Set secret key and allowed hosts in host environment, not source. Run `python manage.py check --deploy` and release smoke tests. Django admin/auth are not part of v1; if framework scaffolding expects a DB, remove unused apps/migrations or configure them so public comparison does not depend on ephemeral SQLite.

Deploy web as static Vite output. Set only public API base URL in its environment. Restrict API CORS to the real Pages origin and authorized preview origins, then test preflight and upload from production. Use HTTPS on both. A CSP and security headers should be verified in deployed responses, not only config files. The recorded synthetic sample is part of the static build and loads even if Render sleeps.

## Expected free-tier behavior

Render documents spin-down after 15 idle minutes and about a minute to wake; its local filesystem is ephemeral. It grants 750 Free instance-hours per workspace per month, and excess included bandwidth/build usage can lead to suspension or disabled builds when no payment method exists. Render states Free web services are for hobby/testing, not production SLA. Do not use its expiring Free Postgres (30-day lifetime) for this stateless v1. Source: [Render Free](https://render.com/docs/free/).

The UI must show an honest waking/retry state with a bounded timeout and retry control. A live request failure remains a failure; it never returns the sample as if it were the uploaded files. Publish a short status/cold-start note near the live compare control and in the README.

## Operations checklist

At release and periodically thereafter, verify: static sample loads; API health; one small live comparison; CORS; report download; current provider usage/free-plan status; error rate/log privacy; dependency advisories; and link health. If Render is suspended or terms change, retain the static sample and local-run instructions and clearly mark live comparison unavailable. Do not add payment details or upgrade automatically. Rotate leaked secrets and redeploy if needed. Keep no uploaded data to back up in v1.

## Rollback

Keep a known-good source commit and generated sample artifact. If a deployment breaks, roll back both UI and API to compatible contract/schema versions using provider-supported rollback or redeploy. Re-run production smoke checks after rollback. A newer sample must never require an incompatible older API for viewing.
