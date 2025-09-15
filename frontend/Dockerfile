# Stage 1: Build the React application
FROM node:20.8.1-alpine AS build

# 빌드 인자들
ARG RUN_TESTS=false

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./

RUN npm ci

COPY . .

# Run tests before building (controlled by build arg)
RUN if [ "$RUN_TESTS" = "true" ] ; then npm test -- --run ; fi

RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.25-alpine@sha256:721fa00bc549df26b3e67cc558ff176112d4ba69847537766f3c28e171d180e7

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# When the container starts, Nginx will serve the files from /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
