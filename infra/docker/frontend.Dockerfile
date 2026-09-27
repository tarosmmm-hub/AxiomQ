# syntax=docker/dockerfile:1.7
ARG NODE_VERSION=22

FROM node:${NODE_VERSION}-alpine AS base
ENV NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /app

FROM base AS deps
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN --mount=type=cache,target=/root/.local/share/pnpm/store pnpm install --frozen-lockfile

# ---- dev: source bind-mounted by docker compose ------------------------------------------------
FROM deps AS dev
COPY frontend/ ./
EXPOSE 3000
CMD ["pnpm", "dev", "--hostname", "0.0.0.0"]

FROM deps AS build
COPY frontend/ ./
RUN pnpm build

# ---- runtime: Next.js standalone output, non-root ---------------------------------------------
FROM node:${NODE_VERSION}-alpine AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
RUN addgroup -g 10001 axiomq && adduser -u 10001 -G axiomq -D axiomq
COPY --from=build --chown=axiomq:axiomq /app/.next/standalone ./
COPY --from=build --chown=axiomq:axiomq /app/.next/static ./.next/static
USER axiomq
EXPOSE 3000
CMD ["node", "server.js"]
