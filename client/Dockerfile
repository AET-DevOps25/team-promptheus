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

# Build standalone bundle (ensure everything runs as root)
COPY . .
RUN pnpm run build

# Ensure proper permissions on build artifacts
RUN chmod -R 755 /app/.next
RUN chmod -R 755 /app/public

FROM base AS runner

# Create user and group first
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Create necessary directories with proper ownership
RUN mkdir -p /app/.next/static && chown -R nextjs:nodejs /app/.next
RUN mkdir -p /app/public && chown -R nextjs:nodejs /app/public

# Copy files with explicit ownership
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Ensure all copied files have correct permissions
RUN chown -R nextjs:nodejs /app
RUN chmod -R 755 /app

# Switch to non-root user only at runtime
USER nextjs

ENV NODE_ENV=production
EXPOSE 8081
ENV PORT=8081
ENV HOSTNAME="0.0.0.0"
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 CMD ["node", "-e", "fetch(`http://localhost:${CLIENT_PORT:-8081}/`).then(x=>x.status==200?process.exit(0):process.exit(1)).catch(()=>process.exit(1))"]
CMD ["node", "server.js"]
