# Stage 1: Build the React application
FROM node:18-alpine as build

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./

RUN npm install

COPY . .

# Run tests before building (controlled by build arg)
ARG RUN_TESTS=false
RUN if [ "$RUN_TESTS" = "true" ] ; then npm test -- --run ; fi

RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:1.25-alpine

COPY --from=build /app/dist /usr/share/nginx/html

# When the container starts, Nginx will serve the files from /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
