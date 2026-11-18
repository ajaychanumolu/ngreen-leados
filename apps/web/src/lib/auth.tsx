"use client";

import { createContext, useContext, useMemo, useState } from "react";

const COOKIE = "leados_demo_token";

type AuthValue = {
  token: string | null;
  setToken: (token: string | null) => void;
};

const AuthContext = createContext<AuthValue | null>(null);

function writeCookie(token: string | null) {
  if (typeof document === "undefined") {
    return;
  }
  if (token) {
    document.cookie = `${COOKIE}=${token}; Path=/; SameSite=Lax`;
    return;
  }
  document.cookie = `${COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function AuthProvider({
  initialToken,
  children,
}: {
  initialToken: string | null;
  children: React.ReactNode;
}) {
  const [token, setTokenState] = useState(initialToken);
  const value = useMemo<AuthValue>(
    () => ({
      token,
      setToken: (next) => {
        setTokenState(next);
        writeCookie(next);
      },
    }),
    [token],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("AuthProvider is missing.");
  }
  return value;
}
