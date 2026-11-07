FROM node:22-alpine@sha256:0e1754758c2df4cfa3e68d59e2e1b7374bb7fd9ea6328eaaacf15cc934af8202 AS base

WORKDIR /app/web
ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS dependencies

COPY web/package.json web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

FROM base AS builder

ARG DJANGO_API_URL=http://api:8000
ENV DJANGO_API_URL=${DJANGO_API_URL}

COPY web/ ./
COPY contracts/openapi.json ../contracts/openapi.json

RUN --mount=type=bind,from=dependencies,source=/app/web/node_modules,target=/app/web/node_modules npm run typegen && npm run build

FROM base AS runner

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs \
    && rm -rf /usr/local/lib/node_modules/npm /usr/local/bin/npm /usr/local/bin/npx

COPY --from=builder --chown=nextjs:nodejs /app/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/web/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/web/public ./public

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
