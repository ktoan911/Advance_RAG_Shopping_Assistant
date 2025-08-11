# Sử dụng Nginx để serve static files
FROM nginx:alpine

# Copy static files vào nginx
COPY . /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Command mặc định của nginx
CMD ["nginx", "-g", "daemon off;"]