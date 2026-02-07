"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();

  const tabs = [
    { label: "Create", href: "/" },
    { label: "History", href: "/history" },
  ];

  return (
    <div className="h-[72px] flex items-center px-6 border-b border-gray-800/50 gap-8">
      <Link
        href="/"
        className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent"
      >
        AI Content Maker
      </Link>
      <nav className="flex gap-1">
        {tabs.map((tab) => {
          const isActive =
            tab.href === "/"
              ? pathname === "/"
              : pathname.startsWith(tab.href);
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
