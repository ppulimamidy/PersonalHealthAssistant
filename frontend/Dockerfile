# Production Dockerfile for Next.js Frontend
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ARG NEXT_PUBLIC_ENABLE_DARK_MODE
ARG NEXT_PUBLIC_ENABLE_OURA
ARG NEXT_PUBLIC_ENABLE_INSIGHTS
ARG NEXT_PUBLIC_ENABLE_DOCTOR_PREP
ARG NEXT_PUBLIC_ENVIRONMENT
ARG NEXT_PUBLIC_APP_VERSION

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL
ENV NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_ENABLE_DARK_MODE=$NEXT_PUBLIC_ENABLE_DARK_MODE
ENV NEXT_PUBLIC_ENABLE_OURA=$NEXT_PUBLIC_ENABLE_OURA
ENV NEXT_PUBLIC_ENABLE_INSIGHTS=$NEXT_PUBLIC_ENABLE_INSIGHTS
ENV NEXT_PUBLIC_ENABLE_DOCTOR_PREP=$NEXT_PUBLIC_ENABLE_DOCTOR_PREP
ENV NEXT_PUBLIC_ENVIRONMENT=$NEXT_PUBLIC_ENVIRONMENT
ENV NEXT_PUBLIC_APP_VERSION=$NEXT_PUBLIC_APP_VERSION

# Disable Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Run the application
CMD ["node", "server.js"]
