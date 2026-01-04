/**
 * Application configuration
 * Modify these values to easily customize the UI and behavior
 */

export const config = {
  app: {
    name: "Opportunity Finder",
    description: "Find opportunities that match your skills and interests",
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

