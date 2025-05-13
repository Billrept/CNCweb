FROM node:18-alpine

WORKDIR /app

# Copy package files first for better layer caching
COPY package.json package-lock.json* ./

# Use npm ci for faster, more reliable installs
RUN npm ci

COPY . .

# Set environment variable for Next.js to watch for file changes
ENV WATCHPACK_POLLING=true

EXPOSE 3000

CMD ["npm", "run", "dev"]