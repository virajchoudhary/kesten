FROM node:22.23.2-alpine3.22 AS base

WORKDIR /app/web
ENV NEXT_TELEMETRY_DISABLED=1

FROM base AS dependencies

COPY web/package.json web/package-lock.json ./
RUN npm ci

FROM base AS builder

ARG DJANGO_API_URL=http://api:8000
ENV DJANGO_API_URL=${DJANGO_API_URL}

COPY --from=dependencies /app/web/node_modules ./node_modules
COPY web/ ./
COPY contracts/openapi.json ../contracts/openapi.json

RUN npm run typegen && npm run build

FROM base AS runner

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/web/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/web/public ./public

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
