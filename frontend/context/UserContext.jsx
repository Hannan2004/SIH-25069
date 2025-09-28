"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { signOut as firebaseSignOut } from "firebase/auth";
import { auth } from "@/lib/firebase";

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem("dc_user");
      if (raw) setUser(JSON.parse(raw));
    } catch {}
    setLoading(false);
  }, []);

  const persist = useCallback((val) => {
    if (val) localStorage.setItem("dc_user", JSON.stringify(val));
    else localStorage.removeItem("dc_user");
  }, []);

  const updateUser = useCallback(
    (partial) => {
      setUser((prev) => {
        const merged = { ...(prev || {}), ...partial };
        persist(merged);
        return merged;
      });
    },
    [persist]
  );

  const setAndStore = useCallback(
    (val) => {
      setUser(val);
      persist(val);
    },
    [persist]
  );

  const signOut = useCallback(async () => {
    try {
      await firebaseSignOut(auth);
    } catch (e) {
      console.warn("signOut error", e);
    }
    setAndStore(null);
  }, [setAndStore]);

  const value = {
    user,
    loading,
    setUser: setAndStore,
    updateUser,
    signOut,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export function useUser() {
  return useContext(UserContext);
}
