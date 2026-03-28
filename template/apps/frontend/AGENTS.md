# Frontend Agent Instructions

## Architecture

```
src/
  app/            ← Next.js App Router (pages, layouts)
  lib/            ← Shared utilities (api-client, cn helper)
  features/       ← Feature modules — ONE folder per backend resource
    <feature>/
      api.ts      ← TanStack Query hooks (useQuery, useMutation)
      schema.ts   ← Zod schemas for form validation
      <Name>List.tsx
      <Name>Form.tsx
      <Name>Detail.tsx  (if needed)
  components/
    ui/           ← shadcn/ui primitives only (Button, Input, Card, etc.)
```

## Rules

### Data fetching
- ALL API calls go through `src/lib/api-client.ts` — never raw `fetch()` anywhere else
- ALL React data fetching uses TanStack Query hooks defined in `features/*/api.ts`
- NEVER call the API client directly from a component — always go through a hook
- Query keys MUST match the resource name: `["items"]`, `["items", id]`
- ALWAYS invalidate relevant queries in `onSuccess` of mutations

### Types
- ALL request/response types come from the generated client (`packages/client/src/types.ts`)
- Import types through `src/lib/api-client.ts`, which re-exports them
- NEVER define a type manually that represents an API shape
- Form types come from Zod inference: `type FormData = z.infer<typeof schema>`

### Components
- Components in `features/` are feature-specific — they import from their sibling `api.ts` and `schema.ts`
- Components in `components/ui/` are generic primitives — they NEVER import from `features/` or `lib/api-client.ts`
- Use `"use client"` directive on any component that uses hooks, event handlers, or browser APIs
- NEVER use `<form>` tags — use `<div>` with `button onClick={handleSubmit(onSubmit)}`

### Forms
- ALWAYS use React Hook Form + Zod resolver
- Schema defined in `features/*/schema.ts`
- Form component uses `useForm<SchemaType>({ resolver: zodResolver(schema) })`
- Submit handler calls the mutation from `api.ts`
- Show validation errors from `formState.errors`
- Reset form on successful submission

### Styling
- Use Tailwind utility classes exclusively
- Use `cn()` helper from `lib/utils.ts` for conditional classes
- NEVER create CSS files or CSS modules
- Follow shadcn/ui patterns for component styling

### Global state (Zustand)
- Use Zustand ONLY for client-side UI state (sidebar, modals, theme, filters)
- NEVER put server data in Zustand — that belongs in TanStack Query
- One store file in `lib/store.ts` for app-wide state
- Feature-specific stores go in `features/*/store.ts` if needed
- ALWAYS use the selector pattern: `useAppStore((s) => s.sidebarOpen)` — never `useAppStore()`

## Adding a new feature

1. Confirm the OpenAPI spec and generated types are up to date (`just generate-client`)
2. Create `src/features/<feature>/` directory
3. Create `api.ts` — copy from `features/items/api.ts`, rename hooks and API calls
4. Create `schema.ts` — define Zod schemas matching the Create/Update shapes
5. Create `<Feature>List.tsx` — copy from `ItemList.tsx`, adapt
6. Create `<Feature>Form.tsx` — copy from `ItemForm.tsx`, adapt
7. Add the feature to a page in `src/app/`
8. Write tests in `tests/<feature>.test.tsx`

## File naming

- Components: `PascalCase.tsx` (e.g., `ItemList.tsx`, `ItemForm.tsx`)
- Hooks/utilities: `camelCase.ts` (e.g., `api.ts`, `schema.ts`)
- Test files: `camelCase.test.tsx` (e.g., `items.test.tsx`)
- Feature directories: `camelCase` (e.g., `features/items/`, `features/userProfiles/`)
