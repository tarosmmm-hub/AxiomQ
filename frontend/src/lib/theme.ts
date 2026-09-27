export type ThemePreference = "light" | "dark" | "system";
export const THEME_STORAGE_KEY = "axq-theme";

/** Runs before first paint (inlined in <head>) to avoid a flash of the wrong theme. */
export const themeBootstrapScript = `(() => {
  try {
    var pref = localStorage.getItem("${THEME_STORAGE_KEY}") || "system";
    var dark = pref === "dark" || (pref === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  } catch (e) {
    document.documentElement.dataset.theme = "dark";
  }
})();`;

export function readThemePreference(): ThemePreference {
  try {
    const value = localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

export function applyThemePreference(pref: ThemePreference): void {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, pref);
  } catch {
    // Storage unavailable (private mode): theme still applies for this page view.
  }
  const dark =
    pref === "dark" ||
    (pref === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}
