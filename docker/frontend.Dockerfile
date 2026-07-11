FROM node:20-alpine AS build

WORKDIR /app

COPY admin-frontend/package.json admin-frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY admin-frontend .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

# nginx-unprivileged: тот же nginx, но изначально настроен на запуск от
# непривилегированного пользователя (uid 101) и слушает порт >1024 (8080) —
# не требует root даже для старта master-процесса (обычный образ nginx,
# в отличие от него, стартует master-процессом от root, хоть и понижает
# привилегии worker-процессов).
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
