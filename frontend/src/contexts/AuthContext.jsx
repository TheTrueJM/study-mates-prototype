import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { BACKEND_URL, getStaffToken, setStaffToken } from "../socket";


const AuthContext = createContext(null);

const STAFF_API = `${BACKEND_URL}/api/staff`;
const SIGNED_OUT = { token: null, staffType: null, username: null };


/** Sends a Request to the Staff API, resolving with { ok, status, data, message } (never throws) */
async function staffRequest(path, options = {}) {
  try {
    const response = await fetch(`${STAFF_API}${path}`, options);
    const data = await response.json().catch(() => ({}));
    return {
      ok: response.ok,
      status: response.status,
      data,
      message: data.message || `Something went wrong (HTTP ${response.status}).`,
    };
  } catch {
    return { ok: false, status: 0, data: {}, message: "Couldn't reach the server. Please try again." };
  }
}


/**
 * Staff use the Application as a Guest or with an Account. Either way the server issues an Access Token,
 * which is validated when the App Loads and whenever the Staff Connection is made.
 */
export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => ({ ...SIGNED_OUT, token: getStaffToken() }));
  // A stored sign in is checked with the server before any staff page is shown
  const [loading, setLoading] = useState(() => !!getStaffToken());

  const applyAuth = useCallback((data) => {
    setStaffToken(data?.token);
    setAuth(data?.token
      ? { token: data.token, staffType: data.staff_type ?? null, username: data.username ?? null }
      : SIGNED_OUT);
  }, []);

  const logout = useCallback(() => applyAuth(null), [applyAuth]);

  useEffect(() => {
    const token = getStaffToken();
    if (!token) return;

    let cancelled = false;
    staffRequest("/me", { headers: { Authorization: `Bearer ${token}` } }).then((response) => {
      if (cancelled) return;

      if (response.ok) applyAuth({ token, ...response.data });
      else if (response.status === 401 || response.status === 422) logout();
      // Otherwise the Server is Unreachable: Keep the Sign In, as the Connection validates it again later

      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [applyAuth, logout]);


  const continueAsGuest = useCallback(async () => {
    const response = await staffRequest("/guest", { method: "POST" });
    if (response.ok && response.data.token) applyAuth(response.data);
    return response;
  }, [applyAuth]);

  const authenticate = useCallback(async (path, username, password) => {
    const response = await staffRequest(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (response.ok && response.data.token) applyAuth(response.data);
    return response;
  }, [applyAuth]);

  const signIn = useCallback((username, password) => authenticate("/login", username, password), [authenticate]);
  const signUp = useCallback((username, password) => authenticate("/register", username, password), [authenticate]);


  const value = useMemo(() => ({
    ...auth,
    isAuthenticated: !!auth.token,
    isGuest: auth.staffType === "guest",
    loading,
    continueAsGuest,
    signIn,
    signUp,
    logout,
  }), [auth, loading, continueAsGuest, signIn, signUp, logout]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
