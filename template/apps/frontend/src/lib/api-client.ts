{% raw %}
// This file wraps the generated OpenAPI types with typed fetch functions.
// After running `just generate-client`, the types in packages/client/src/types.ts
// are the source of truth for all API shapes.
//
// IMPORTANT: When adding a new feature, add new functions here following
// the same pattern. Never use raw fetch() in components.

import type { paths } from "../../../../packages/client/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Item = paths["/api/items"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ItemCreate = paths["/api/items"]["post"]["requestBody"]["content"]["application/json"];
type ItemUpdate = paths["/api/items/{item_id}"]["put"]["requestBody"]["content"]["application/json"];

export type { Item, ItemCreate, ItemUpdate };

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const itemsApi = {
  list: (skip = 0, limit = 100) =>
    apiFetch<Item[]>(`/api/items/?skip=${skip}&limit=${limit}`),

  get: (id: number) =>
    apiFetch<Item>(`/api/items/${id}`),

  create: (data: ItemCreate) =>
    apiFetch<Item>("/api/items/", { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: ItemUpdate) =>
    apiFetch<Item>(`/api/items/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  delete: (id: number) =>
    apiFetch<void>(`/api/items/${id}`, { method: "DELETE" }),
};
{% endraw %}
