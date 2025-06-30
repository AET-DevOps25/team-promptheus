FROM --platform=$BUILDPLATFORM node:24-slim AS base
WORKDIR /app

FROM base AS builder

# Install pnpm
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable pnpm

# Install dependencies
COPY package.json ./
COPY pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# build standalone bundle
COPY . .
RUN pnpm run build

FROM base AS runner

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

ENV NODE_ENV=production
EXPOSE 8081
ENV PORT=8081
ENV HOSTNAME="0.0.0.0"
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD ["node", "-e", "fetch(`http://localhost:${CLIENT_PORT:-8081}/`).then(x=>x.status==200?process.exit(0):process.exit(1)).catch(()=>process.exit(1))"]
CMD ["node", "server.js"]
