{% raw %}
import { ItemList } from "@/features/items/ItemList";
import { ItemForm } from "@/features/items/ItemForm";

export default function Home() {
  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-8 text-2xl font-bold">{% endraw %}{{ project_name }}{% raw %}</h1>
      <ItemForm />
      <div className="mt-8">
        <ItemList />
      </div>
    </main>
  );
}
{% endraw %}
