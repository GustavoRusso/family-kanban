FROM node:22-alpine AS build
WORKDIR /app

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app

ENV HOST=0.0.0.0 \
	PORT=80

COPY --from=build /app/.output ./.output

EXPOSE 80
CMD ["node", ".output/server/index.mjs"]
