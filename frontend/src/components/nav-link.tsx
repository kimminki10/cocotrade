"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const active = usePathname() === href;
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`text-ink underline-offset-[6px] hover:text-accent ${active ? "underline" : "no-underline"}`}
    >
      {children}
    </Link>
  );
}
