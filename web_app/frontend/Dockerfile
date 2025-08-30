# ---------- build ----------
FROM node:18-bullseye AS builder
WORKDIR /app
RUN npm config set registry https://registry.npmmirror.com
COPY package*.json ./
RUN npm ci
COPY . .
# CRA -> build，Vite -> dist，这里统一成 build 目录
RUN npm run build && if [ -d dist ]; then mv dist build; fi

# ---------- runtime ----------
FROM nginx:1.25-bullseye
# 放置前端产物
COPY --from=builder /app/build /usr/share/nginx/html
# 拷贝你的 nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1
CMD ["nginx", "-g", "daemon off;"]
