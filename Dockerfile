# ---------- build stage ----------
FROM node:20-slim AS build
WORKDIR /app

# Copy dependencies first (caching enabled)
COPY package.json package-lock.json* ./
# There are environments without lock, so use install (if ci is fixed, EUSAGE may occur)
RUN npm install

# Copy the source and build
COPY tsconfig.json ./
COPY src ./src
RUN npm run build

# Prepare a separate node_modules package that excludes dev dependencies not needed at runtime.
# (This configuration prevents reinstallation at runtime.)
RUN npm prune --omit=dev

# ---------- runtime stage ----------
FROM node:20-slim AS runtime
WORKDIR /app

# Copy only the artifacts required for execution
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist

# Start (JS)
CMD ["node", "dist/server.js"]
