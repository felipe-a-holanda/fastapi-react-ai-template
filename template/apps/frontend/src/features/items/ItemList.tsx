{% raw %}
"use client";

import { useItems, useDeleteItem, useUpdateItem } from "./api";

export function ItemList() {
  const { data: items, isLoading, error } = useItems();
  const deleteItem = useDeleteItem();
  const updateItem = useUpdateItem();

  if (isLoading) return <div className="py-4 text-gray-500">Loading...</div>;
  if (error) return <div className="py-4 text-red-500">Error: {error.message}</div>;
  if (!items?.length) return <div className="py-4 text-gray-500">No items yet.</div>;

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-center justify-between rounded border p-3"
        >
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={item.is_completed}
              onChange={() =>
                updateItem.mutate({
                  id: item.id,
                  data: { is_completed: !item.is_completed },
                })
              }
              className="h-4 w-4"
            />
            <span className={item.is_completed ? "line-through text-gray-400" : ""}>
              {item.title}
            </span>
          </div>
          <button
            type="button"
            onClick={() => deleteItem.mutate(item.id)}
            className="text-sm text-red-500 hover:text-red-700"
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
{% endraw %}
