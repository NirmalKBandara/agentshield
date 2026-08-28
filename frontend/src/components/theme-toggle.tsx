"use client";

import { useEffect, useRef, useState } from "react";

type Theme = "light" | "dark" | "system";

function applyTheme(theme: Theme) {
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.dataset.theme = theme === "system" ? (prefersDark ? "dark" : "light") : theme;
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");
  const themeRef = useRef<Theme>("system");

  useEffect(() => {
    const stored = localStorage.getItem("agentshield-theme") as Theme | null;
    const initial = stored && ["light", "dark", "system"].includes(stored) ? stored : "system";
    // This client-only hydration synchronizes React with the persisted browser preference.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(initial);
    themeRef.current = initial;
    applyTheme(initial);
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => themeRef.current === "system" && applyTheme("system");
    media.addEventListener("change", handleChange);
    return () => media.removeEventListener("change", handleChange);
  }, []);

  function updateTheme(nextTheme: Theme) {
    setTheme(nextTheme);
    themeRef.current = nextTheme;
    localStorage.setItem("agentshield-theme", nextTheme);
    applyTheme(nextTheme);
  }

  return (
    <label className="theme-control">
      <span>Theme</span>
      <select value={theme} onChange={(event) => updateTheme(event.target.value as Theme)}>
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
    </label>
  );
}
