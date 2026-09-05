"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "./theme-toggle";

const destinations = [
  ["/", "Home"],
  ["/dashboard", "Dashboard"],
  ["/playground", "Agent Playground"],
  ["/security-events", "Security Events"],
  ["/tool-calls", "Tool Calls"],
  ["/policies", "Security Policies"],
  ["/red-team", "Red Team Lab"],
] as const;

export function AppNavigation() {
  const pathname = usePathname();
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="app-header">
        <div className="app-header__top">
          <Link className="brand" href="/">Agent<span>Shield</span></Link>
          <ThemeToggle />
        </div>
        <nav className="app-navigation" aria-label="Main navigation">
          {destinations.map(([href, label]) => (
            <Link key={href} href={href} aria-current={pathname === href ? "page" : undefined}>
              {label}
            </Link>
          ))}
        </nav>
      </header>
    </>
  );
}
