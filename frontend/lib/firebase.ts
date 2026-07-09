import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import { getAuth, type Auth } from "firebase/auth";

// Centralized Firebase client initialization — this is the only place
// initializeApp()/getAuth() should be called. Every other module imports
// getFirebaseAuth() instead of touching the Firebase SDK directly.
//
// Firebase web config is not a server secret (it's visible in any deployed
// bundle by design — access control lives in Firebase Auth + Firestore
// rules, not in hiding this config), but it's still environment-specific,
// so it's threaded through NEXT_PUBLIC_* env vars for dev/staging/prod
// separation rather than hardcoded.
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

export function isFirebaseConfigured(): boolean {
  return Boolean(
    firebaseConfig.apiKey && firebaseConfig.projectId && firebaseConfig.appId,
  );
}

let cachedApp: FirebaseApp | null = null;

export function getFirebaseApp(): FirebaseApp | null {
  if (!isFirebaseConfigured()) return null;

  if (!cachedApp) {
    cachedApp = getApps().length ? getApps()[0]! : initializeApp(firebaseConfig);
  }

  return cachedApp;
}

export function getFirebaseAuth(): Auth | null {
  const app = getFirebaseApp();
  if (!app) return null;
  return getAuth(app);
}
