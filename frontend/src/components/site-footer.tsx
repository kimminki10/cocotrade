import { copy } from "@/content/copy";

export function SiteFooter() {
  return (
    <footer className="mt-16 max-w-3xl border-t border-rule pt-5 pb-10 text-sm leading-relaxed text-muted">
      {copy.disclaimer}
    </footer>
  );
}
