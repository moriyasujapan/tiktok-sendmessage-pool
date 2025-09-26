FROM node:20-slim

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev || npm i --omit=dev

COPY tsconfig.json ./
COPY src ./src

ENV NODE_ENV=production

CMD ["node", "--version"]

