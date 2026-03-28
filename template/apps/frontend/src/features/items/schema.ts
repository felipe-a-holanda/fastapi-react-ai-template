{% raw %}
import { z } from "zod";

export const itemCreateSchema = z.object({
  title: z.string().min(1, "Title is required").max(255),
  description: z.string().nullable().optional(),
});

export const itemUpdateSchema = z.object({
  title: z.string().min(1).max(255).optional(),
  description: z.string().nullable().optional(),
  is_completed: z.boolean().optional(),
});

export type ItemCreateForm = z.infer<typeof itemCreateSchema>;
export type ItemUpdateForm = z.infer<typeof itemUpdateSchema>;
{% endraw %}
