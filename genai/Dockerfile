# Base stage for installing dependencies
FROM node:22-slim AS base
ARG NODE_ENV=production
WORKDIR /usr/src/app

# Install dependencies
COPY package*.json ./
RUN npm install

FROM node:22-slim AS prod
WORKDIR /usr/src/app

# Install curl
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies from base stage
COPY --from=base /usr/src/app/node_modules ./node_modules
COPY tsconfig.json ./
COPY package*.json ./

# Copy application code and build
COPY . .

# Expose port and start production server
EXPOSE ${GENAI_PORT:-3003}
CMD ["npm", "run", "start"]
