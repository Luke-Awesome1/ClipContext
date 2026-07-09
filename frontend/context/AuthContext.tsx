"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  type User as FirebaseUser,
} from "firebase/auth";
import { getFirebaseAuth, isFirebaseConfigured } from "@/lib/firebase";

// ClipContext account identity (Firebase Authentication) — distinct from
// YouTube OAuth connection state (see YouTubeUploadPanel/useYouTubeUploadPolling).
// A user can be logged into ClipContext with one Google account and have
// authorized YouTube uploads through a different one; nothing here assumes
// those are the same identity.
export interface AuthUser {
  uid: string;
  displayName: string | null;
  email: string | null;
  photoURL: string | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  firebaseConfigured: boolean;
  loginWithGoogle: () => Promise<AuthUser>;
  signupWithGoogle: () => Promise<AuthUser>;
  logout: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function toAuthUser(firebaseUser: FirebaseUser): AuthUser {
  return {
    uid: firebaseUser.uid,
    displayName: firebaseUser.displayName,
    email: firebaseUser.email,
    photoURL: firebaseUser.photoURL,
  };
}

function friendlyAuthError(err: unknown): Error {
  const code = (err as { code?: string } | null)?.code;

  if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") {
    return new Error("Sign-in was cancelled.");
  }
  if (code === "auth/popup-blocked") {
    return new Error(
      "Your browser blocked the sign-in popup. Please allow popups and try again.",
    );
  }
  if (code === "auth/user-disabled") {
    return new Error("This account has been disabled.");
  }
  if (code === "auth/network-request-failed") {
    return new Error("Network error during sign-in. Please try again.");
  }

  return new Error("Sign-in failed. Please try again.");
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const firebaseConfigured = isFirebaseConfigured();

  // Firebase Auth is browser-only; this effect never runs during Next.js
  // server rendering, only after the component mounts client-side.
  useEffect(() => {
    const auth = getFirebaseAuth();

    if (!auth) {
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser ? toAuthUser(firebaseUser) : null);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const withGoogle = useCallback(async (): Promise<AuthUser> => {
    const auth = getFirebaseAuth();

    if (!auth) {
      throw new Error("Sign-in is not available right now.");
    }

    try {
      const provider = new GoogleAuthProvider();
      const credential = await signInWithPopup(auth, provider);
      return toAuthUser(credential.user);
    } catch (err) {
      throw friendlyAuthError(err);
    }
  }, []);

  const logout = useCallback(async () => {
    const auth = getFirebaseAuth();
    if (!auth) return;
    await signOut(auth);
  }, []);

  const getIdToken = useCallback(async (): Promise<string | null> => {
    const auth = getFirebaseAuth();
    if (!auth?.currentUser) return null;
    return auth.currentUser.getIdToken();
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      firebaseConfigured,
      loginWithGoogle: withGoogle,
      signupWithGoogle: withGoogle,
      logout,
      getIdToken,
    }),
    [user, loading, firebaseConfigured, withGoogle, logout, getIdToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
