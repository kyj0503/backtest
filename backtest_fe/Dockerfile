# Stage 1: Build the React application
FROM node:20.8.1-alpine AS build

WORKDIR /app

# Copy only package manifests first to leverage Docker layer caching
COPY package*.json ./

# Install dependencies in CI-friendly mode when lockfile exists, otherwise fall back to npm install
RUN if [ -f package-lock.json ]; then \
			npm ci --no-audit --prefer-offline --no-fund; \
		else \
			npm install --no-audit --prefer-offline --no-fund; \
		fi

# Copy rest of sources
COPY . .

# Build production assets
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# When the container starts, Nginx will serve the files from /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
