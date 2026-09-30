import Link from "next/link";
import { copy } from "@/content/copy";
import { NavLink } from "./nav-link";

export function SiteHeader() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-rule sm:h-19">
      <Link href="/" className="font-serif text-2xl font-semibold text-ink no-underline">
        {copy.site.name}
      </Link>
      <nav className="flex gap-6 text-base sm:gap-7">
        <NavLink href="/backtest">{copy.nav.backtest}</NavLink>
        <NavLink href="/compare">{copy.nav.compare}</NavLink>
      </nav>
    </header>
  );
}
