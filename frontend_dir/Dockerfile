FROM node
WORKDIR /app
COPY frontend_dir/package*.json ./
RUN npm install
COPY frontend_dir/ /app
COPY .env /app
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
