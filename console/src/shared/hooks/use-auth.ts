import { useAuth as useWorkOSAuth } from "@workos-inc/authkit-react";

const NOOP_AUTH = {
  user: null,
  isLoading: false,
  signIn: () => {
    console.warn("WorkOS not configured. Set VITE_WORKOS_CLIENT_ID in .env.local");
  },
  signOut: () => Promise.resolve(),
  getAccessToken: () => Promise.resolve(""),
} as const;

function useWorkOSHook() {
  const { user, isLoading, signIn, signOut, getAccessToken } = useWorkOSAuth();
  return { user, isLoading, signIn, signOut, getAccessToken };
}

function useNoopHook() {
  return NOOP_AUTH;
}

export const useAuth = import.meta.env.VITE_WORKOS_CLIENT_ID
  ? useWorkOSHook
  : useNoopHook;
