# 1. Build Stage - React + Vite

FROM node:18 AS builder
WORKDIR /app
# 패키지 파일 복사 (cache 최적화)
COPY package*.json ./
RUN npm install
COPY . .
# React(Vite) 빌드
RUN npm run build



# 2. Serve Stage - Nginx
FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
