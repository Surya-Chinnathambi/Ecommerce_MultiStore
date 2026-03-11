# Storefront Dockerfile
FROM node:18-alpine AS build

WORKDIR /app

# Build-time environment variables (baked into the bundle by Vite)
# Override with: docker build --build-arg VITE_API_URL=https://yourdomain.com/api/v1
ARG VITE_API_URL=/api/v1
ARG VITE_WS_URL=ws://localhost/api/v1
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_WS_URL=${VITE_WS_URL}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --prefer-offline --legacy-peer-deps

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage — serve with nginx
FROM nginx:1.25-alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
