---
name: winternight-web-deploy
description: Build, publish, invalidate, and verify the Winternight browser POC on its production S3 and CloudFront custom domain using the AWS personal profile. Use when asked to deploy, publish, ship, or update the live Winternight web build; do not use the unrelated dash-perform/Vercel deploy workflow.
---

# Winternight Web Deploy

Deploy from `/home/chris/git/wot-game`. This workflow intentionally publishes the current working tree after verification; it is not a committed-HEAD release workflow.

## Production target

- URL: `https://wot-game.arcadian.cloud/`
- S3 origin: `s3://winternight-rpg-poc-chrishart0/`
- CloudFront distribution: `E1V1AX0S4NBYGI` (`d1t6pnc0m8ia3g.cloudfront.net`)
- Route 53 hosted zone: `ZPUEIPB6QNCF` (`arcadian.cloud`)
- Region: `us-east-1`
- AWS profile: `personal`
- Upload boundary: contents of `build/web-app/build/web/` only

Never upload the repository, `source/private/`, saves, logs, `dist/`, credentials, or the parent `build/` tree.

## Workflow

1. Verify the current project before publication:

   ```bash
   make check
   ```

   A previously completed `make check` from the same unchanged project tree is acceptable when its hash is recorded in `EXEC_PLAN.md`. Otherwise run it now.

2. Build the browser payload:

   ```bash
   make web-build
   ```

   Confirm the staged project tree hash printed by `winternight web-stage` is the intended current hash. Confirm `build/web-app/build/web/` contains only the static browser payload: Pygbag archives/runtime files plus the manifest, service worker, favicon, splash, and PWA icons.

3. Verify AWS identity with the required profile:

   ```bash
   aws sts get-caller-identity --profile personal
   ```

   Expected account: `933784155053`. If SSO is expired, run `aws sso login --profile personal`, complete authorization, and retry identity verification. Never fall back to the default AWS profile.

4. Publish exactly the static payload:

   ```bash
   aws s3 sync build/web-app/build/web/ \
     s3://winternight-rpg-poc-chrishart0/ \
     --delete \
     --region us-east-1 \
     --profile personal
   ```

5. Invalidate CloudFront so the custom domain serves the new immutable build immediately:

   ```bash
   INVALIDATION_ID="$(aws cloudfront create-invalidation \
     --distribution-id E1V1AX0S4NBYGI \
     --paths '/*' \
     --profile personal \
     --query 'Invalidation.Id' \
     --output text)"
   aws cloudfront wait invalidation-completed \
     --distribution-id E1V1AX0S4NBYGI \
     --id "$INVALIDATION_ID" \
     --profile personal
   ```

6. Verify deployed bytes. Read S3 metadata for `web-app.tar.gz` and compare its ETag with the local MD5; these objects are uploaded as single parts:

   ```bash
   aws s3api head-object \
     --bucket winternight-rpg-poc-chrishart0 \
     --key web-app.tar.gz \
     --region us-east-1 \
     --profile personal
   md5sum build/web-app/build/web/web-app.tar.gz
   ```

   The quoted ETag and local MD5 must match.

7. Verify the live application in Chromium at `https://wot-game.arcadian.cloud/`:

   - HTTPS certificate is valid for `wot-game.arcadian.cloud`;
   - no failed `web-app` resource requests;
   - `web-app.tar.gz` downloads with nonzero bytes;
   - canvas initializes at native `480×320`;
   - document title becomes `Eye of the World - v2026.02.17a` (or the intentionally updated pinned version);
   - the visible viewport renders the Eye of the World title and `PRESS START` rather than a loader, traceback, or blank canvas;
   - the service-worker scope is `https://wot-game.arcadian.cloud/`.

   Capture a live screenshot as deployment evidence.

8. Record the deploy in `EXEC_PLAN.md`: project tree hash, project-manifest hash, bucket object version/ETag, CloudFront distribution/invalidation, production URL, and live-browser result. Do not claim a gameplay smoke beyond what was actually exercised.

## Failure handling

- Build/test failure: do not sync.
- Wrong AWS account/profile: stop; do not deploy.
- SSO expiry: authenticate only `--profile personal`.
- S3 sync failure: report partial publication risk and retry the complete sync after credentials/network recover.
- CloudFront invalidation failure: do not report the custom domain as updated; retry the invalidation and wait for completion.
- ETag mismatch, TLS failure, or blank/failed canvas: deployment is not verified; investigate and republish before reporting success.
- This public POC remains subject to the provenance and legal risks recorded in `EXEC_PLAN.md`; deployment does not waive them.
