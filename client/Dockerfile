# syntax=docker.io/docker/dockerfile:1
FROM --platform=$BUILDPLATFORM node:24-slim AS base
WORKDIR /app
FROM base AS builder

# Install dependencies
COPY package*.json ./
RUN  npm ci
COPY *.json ./
COPY *.ts ./
COPY *.html ./
COPY src src
COPY public/* public/

RUN npm run build

FROM nginx:1-alpine-slim as prod
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf  /etc/nginx/conf.d
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
