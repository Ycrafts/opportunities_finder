export const POST_AUTH_REDIRECT_KEY = "findra:post_auth_redirect";

export const setPostAuthRedirect = (path: string) => {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(POST_AUTH_REDIRECT_KEY, path);
  } catch {
    // ignore
  }
};

export const consumePostAuthRedirect = (): string | null => {
  if (typeof window === "undefined") return null;
  try {
    const value = sessionStorage.getItem(POST_AUTH_REDIRECT_KEY);
    if (value) {
      sessionStorage.removeItem(POST_AUTH_REDIRECT_KEY);
      return value;
    }
  } catch {
    // ignore
  }
  return null;
};

export const sanitizeInternalRedirectPath = (path: string | null): string | null => {
  if (!path) return null;

  // Disallow protocol-relative/absolute URLs to prevent open redirects.
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("//")) {
    return null;
  }

  // Only allow internal relative paths.
  if (!path.startsWith("/")) {
    return null;
  }

  // Prevent backslash weirdness.
  if (path.includes("\\")) {
    return null;
  }

  // Basic hardening: avoid newlines.
  if (path.includes("\n") || path.includes("\r")) {
    return null;
  }

  return path;
};
