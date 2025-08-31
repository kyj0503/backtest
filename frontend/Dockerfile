# Stage 1: Build the React application
FROM node:18-alpine as build

# 빌드 인자들
ARG RUN_TESTS=false
ARG GIT_COMMIT=unknown
ARG GIT_BRANCH=unknown
ARG BUILD_NUMBER=unknown

# 환경변수로 설정 (빌드 시점에 코드에 포함됨)
ENV GIT_COMMIT=${GIT_COMMIT}
ENV GIT_BRANCH=${GIT_BRANCH}
ENV BUILD_NUMBER=${BUILD_NUMBER}

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./

RUN npm install

COPY . .

# Run tests before building (controlled by build arg)
RUN if [ "$RUN_TESTS" = "true" ] ; then npm test -- --run ; fi

RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.25-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# When the container starts, Nginx will serve the files from /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
