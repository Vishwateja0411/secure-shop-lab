FROM nginx:alpine

# Remove default nginx configurations
RUN rm -rf /etc/nginx/conf.d/default.conf

# Copy custom reverse proxy config
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend static files
COPY frontend /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
