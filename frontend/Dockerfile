FROM node:24-slim

# Enable pnpm via corepack. Pin the version so image builds are reproducible.
RUN corepack enable && corepack prepare pnpm@11.17.0 --activate

WORKDIR /app

# Install dependencies (layer cached).
# pnpm-workspace.yaml carries the install settings (onlyBuiltDependencies,
# allowBuilds) that pnpm 10+ no longer reads from package.json. Without it
# @sentry/cli's postinstall is silently skipped and its binary never lands.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

EXPOSE 5173

CMD ["pnpm", "dev", "--host", "0.0.0.0"]
