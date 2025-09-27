# ---------- build stage ----------
FROM node:20-slim AS build

WORKDIR /app

RUN apt-get update && apt-get install -y wget gnupg python3 python3-venv python3-pip \
 && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && apt-get install -y ./google-chrome-stable_current_amd64.deb \
 && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/google-chrome

COPY package.json package-lock.json* ./
RUN npm install

COPY tsconfig.json ./
COPY src ./src
RUN npm run build
RUN npm prune --omit=dev

# ---------- runtime stage ----------
FROM node:20-slim AS runtime
WORKDIR /app

COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist

CMD ["node", "dist/server.js"]
