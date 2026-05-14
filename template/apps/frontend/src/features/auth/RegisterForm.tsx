{% raw -%}
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { registerSchema, type RegisterForm } from "./schema";
import { useRegister } from "./api";

export function RegisterForm({ onSuccess }: { onSuccess?: () => void }) {
  const register = useRegister();

  const form = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", full_name: "" },
  });

  const onSubmit = (data: RegisterForm) => {
    register.mutate(data, { onSuccess });
  };

  return (
    <div className="mx-auto max-w-sm space-y-4 rounded-lg border p-6">
      <h2 className="text-xl font-semibold">Register</h2>
      {register.error && (
        <p className="text-sm text-red-500">{register.error.message}</p>
      )}
      <div className="space-y-3">
        <div>
          <input
            {...form.register("full_name")}
            placeholder="Full name (optional)"
            className="w-full rounded border px-3 py-2"
          />
        </div>
        <div>
          <input
            {...form.register("email")}
            type="email"
            placeholder="Email"
            className="w-full rounded border px-3 py-2"
          />
          {form.formState.errors.email && (
            <p className="mt-1 text-sm text-red-500">
              {form.formState.errors.email.message}
            </p>
          )}
        </div>
        <div>
          <input
            {...form.register("password")}
            type="password"
            placeholder="Password (min 8 characters)"
            className="w-full rounded border px-3 py-2"
          />
          {form.formState.errors.password && (
            <p className="mt-1 text-sm text-red-500">
              {form.formState.errors.password.message}
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={form.handleSubmit(onSubmit)}
          disabled={register.isPending}
          className="w-full rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
        >
          {register.isPending ? "Creating account..." : "Register"}
        </button>
      </div>
    </div>
  );
}
{% endraw %}
