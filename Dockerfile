# ========================================
# Base Image (Debian-based)
# ========================================
FROM node:iron-trixie-slim AS base


WORKDIR /app


# Create non-root user (Debian)
RUN groupadd -g 1001 nodejs \
   && useradd -u 1001 -g nodejs -m nodejs \
   && chown -R nodejs:nodejs /app


# ========================================
# Dependencies Stage
# ========================================
FROM base AS deps


COPY package*.json ./


RUN --mount=type=cache,target=/root/.npm,sharing=locked \
   npm ci --omit=dev && npm cache clean --force


# ========================================
# Build Dependencies Stage
# ========================================
FROM base AS build-deps


COPY package*.json ./


RUN --mount=type=cache,target=/root/.npm,sharing=locked \
   npm ci --no-audit --no-fund && npm cache clean --force


# ========================================
# Build Stage
# ========================================
FROM build-deps AS build


COPY --chown=nodejs:nodejs . .


RUN npm run build


# ========================================
# Development Stage
# ========================================
FROM build-deps AS development


ENV NODE_ENV=development


COPY . .


RUN chown -R nodejs:nodejs /app


USER nodejs


EXPOSE 3000 5173 9229


CMD ["npm", "run", "dev:docker"]


# ========================================
# Production Stage
# ========================================
FROM node:iron-trixie-slim AS production


WORKDIR /app


# Create same non-root user
RUN groupadd -g 1001 nodejs \
   && useradd -u 1001 -g nodejs -m nodejs \
   && chown -R nodejs:nodejs /app


ENV NODE_ENV=production \
   NODE_OPTIONS="--max-old-space-size=256 --no-warnings" \
   NPM_CONFIG_LOGLEVEL=silent


COPY --from=deps --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=deps --chown=nodejs:nodejs /app/package*.json ./
COPY --from=build --chown=nodejs:nodejs /app/dist ./dist


USER nodejs


EXPOSE 3000


CMD ["node", "dist/server.js"]


# ========================================
# Test Stage
# ========================================
FROM build-deps AS test


ENV NODE_ENV=test \
   CI=true


COPY --chown=nodejs:nodejs . .


USER nodejs


CMD ["npm", "run", "test:coverage"]



