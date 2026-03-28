{% raw %}
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { itemsApi, type ItemCreate, type ItemUpdate } from "@/lib/api-client";

const ITEMS_KEY = ["items"] as const;

export function useItems() {
  return useQuery({
    queryKey: ITEMS_KEY,
    queryFn: () => itemsApi.list(),
  });
}

export function useItem(id: number) {
  return useQuery({
    queryKey: [...ITEMS_KEY, id],
    queryFn: () => itemsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ItemCreate) => itemsApi.create(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}

export function useUpdateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ItemUpdate }) =>
      itemsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => itemsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}
{% endraw %}
