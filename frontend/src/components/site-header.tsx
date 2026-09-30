import Link from "next/link";
import { copy } from "@/content/copy";

export function SiteHeader() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-rule sm:h-19">
      <Link href="/" className="font-serif text-2xl font-semibold text-ink no-underline">
        {copy.site.name}
      </Link>
    </header>
  );
}
