{% raw -%}
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { loginSchema, type LoginForm } from "./schema";
import { useLogin } from "./api";

export function LoginForm({ onSuccess }: { onSuccess?: () => void }) {
  const login = useLogin();

  const form = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = (data: LoginForm) => {
    login.mutate(data, { onSuccess });
  };

  return (
    <div className="mx-auto max-w-sm space-y-4 rounded-lg border p-6">
      <h2 className="text-xl font-semibold">Login</h2>
      {login.error && (
        <p className="text-sm text-red-500">{login.error.message}</p>
      )}
      <div className="space-y-3">
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
            placeholder="Password"
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
          disabled={login.isPending}
          className="w-full rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {login.isPending ? "Logging in..." : "Login"}
        </button>
      </div>
    </div>
  );
}
{% endraw %}
