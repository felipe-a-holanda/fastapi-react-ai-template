{% raw %}
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { itemCreateSchema, type ItemCreateForm } from "./schema";
import { useCreateItem } from "./api";

export function ItemForm() {
  const createItem = useCreateItem();

  const form = useForm<ItemCreateForm>({
    resolver: zodResolver(itemCreateSchema),
    defaultValues: { title: "", description: "" },
  });

  const onSubmit = (data: ItemCreateForm) => {
    createItem.mutate(data, {
      onSuccess: () => form.reset(),
    });
  };

  return (
    <div className="space-y-4 rounded-lg border p-4">
      <h2 className="text-lg font-semibold">New Item</h2>
      {/* NOTE: Do NOT use <form> tags in artifacts/React.
          Use div + button onClick instead. */}
      <div className="space-y-3">
        <div>
          <input
            {...form.register("title")}
            placeholder="Item title"
            className="w-full rounded border px-3 py-2"
          />
          {form.formState.errors.title && (
            <p className="mt-1 text-sm text-red-500">
              {form.formState.errors.title.message}
            </p>
          )}
        </div>
        <div>
          <textarea
            {...form.register("description")}
            placeholder="Description (optional)"
            className="w-full rounded border px-3 py-2"
            rows={3}
          />
        </div>
        <button
          type="button"
          onClick={form.handleSubmit(onSubmit)}
          disabled={createItem.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {createItem.isPending ? "Creating..." : "Create Item"}
        </button>
      </div>
    </div>
  );
}
{% endraw %}
