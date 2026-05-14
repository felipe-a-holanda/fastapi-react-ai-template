{% raw -%}
"use client";

import { useCurrentUser, useLogout } from "@/features/auth/api";
import { LoginForm } from "@/features/auth/LoginForm";
import { RegisterForm } from "@/features/auth/RegisterForm";
import { ItemList } from "@/features/items/ItemList";
import { ItemForm } from "@/features/items/ItemForm";
import { useState } from "react";

export default function Home() {
  const { data: user, isLoading } = useCurrentUser();
  const logout = useLogout();
  const [showRegister, setShowRegister] = useState(false);

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-4">
          {showRegister ? (
            <>
              <RegisterForm onSuccess={() => setShowRegister(false)} />
              <p className="text-center text-sm text-gray-500">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => setShowRegister(false)}
                  className="text-blue-600 hover:underline"
                >
                  Login
                </button>
              </p>
            </>
          ) : (
            <>
              <LoginForm />
              <p className="text-center text-sm text-gray-500">
                Don&apos;t have an account?{" "}
                <button
                  type="button"
                  onClick={() => setShowRegister(true)}
                  className="text-blue-600 hover:underline"
                >
                  Register
                </button>
              </p>
            </>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Items</h1>
          <p className="text-sm text-gray-500">{user.email}</p>
        </div>
        <button
          type="button"
          onClick={() => logout.mutate()}
          className="rounded border px-3 py-1 text-sm hover:bg-gray-50"
        >
          Logout
        </button>
      </div>
      <ItemForm />
      <div className="mt-8">
        <ItemList />
      </div>
    </main>
  );
}
{% endraw %}
