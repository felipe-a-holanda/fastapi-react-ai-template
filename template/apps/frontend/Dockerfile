FROM node:{{ node_version }}-slim

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

{% raw %}
CMD ["pnpm", "start"]
{% endraw %}
