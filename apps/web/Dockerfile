# Build from the repo root: docker build -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=... .
FROM oven/bun:1.4.4-alpine AS build
WORKDIR /repo
COPY package.json bun.lock ./
COPY apps/web/package.json apps/web/
COPY apps/admin/package.json apps/admin/
COPY packages/ui/package.json packages/ui/
COPY packages/i18n/package.json packages/i18n/
COPY packages/api-client/package.json packages/api-client/
RUN --mount=type=cache,target=/root/.bun/install/cache bun install --frozen-lockfile
COPY packages packages
COPY apps/web apps/web
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_TG_BOT
ARG NEXT_PUBLIC_MEDIA_URL=https://media.dtm-ai.uz
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_PUBLIC_TG_BOT=$NEXT_PUBLIC_TG_BOT NEXT_PUBLIC_MEDIA_URL=$NEXT_PUBLIC_MEDIA_URL NEXT_TELEMETRY_DISABLED=1
RUN bun run --filter @dtmai/web build

FROM nginx:1.30.6-alpine
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/apps/web/out /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO /dev/null http://127.0.0.1/ || exit 1
