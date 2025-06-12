

FROM node:22-slim AS base
WORKDIR /app



#### BUILD container

FROM base AS builder

# Install dependencies based on the preferred package manager
COPY pulse-front/package*.json ./
COPY pulse-front/package-lock.json ./
RUN  npm ci
COPY pulse-front/. .

RUN npm install
#RUN npm run build  # not yet


#### RUN container
FROM base AS runner
WORKDIR /app

COPY pulse-front/package*.json ./
COPY pulse-front/package-lock.json ./
COPY pulse-front/. .

ENV NODE_ENV=production
#ENV NEXT_TELEMETRY_DISABLED=1

#RUN addgroup --system --gid 1001 nodejs
#RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
#COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
#COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

#USER nextjs

# 3000
EXPOSE 8080 
ENV PORT=8080 

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/config/next-config-js/output
ENV HOSTNAME="0.0.0.0"
#CMD ["node", "server.js"]

CMD ["npm", "run", "dev"]
