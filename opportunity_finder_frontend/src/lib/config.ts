/**
 * Application configuration
 * Modify these values to easily customize the UI and behavior
 */

export const config = {
  app: {
    name: "Opportunity Finder",
    description: "Precise matching for jobs, internships, scholarships, and professional growth",
  },
  theme: {
    defaultTheme: "system" as "light" | "dark" | "system",
    enableSystem: true,
  },
  features: {
    enableAuth: true,
    enableNotifications: true,
  },
} as const

