"use client";

import { usePathname } from "next/navigation";
import { NavActions } from "@/components/nav-actions";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";

// Client component for dynamic header with breadcrumb
export function Header() {
  const pathname = usePathname();

  // Map paths to page titles
  const getPageTitle = (path: string): string => {
    switch (path) {
      case "/":
        return "Home";
      case "/chat":
        return "Ask AI";
      case "/library":
        return "Library";
      case "/settings":
        return "Settings";
      default:
        return "Buddhi AI"; // Default fallback title
    }
  };

  return (
    <header className="flex h-14 shrink-0 items-center gap-2">
      <div className="flex flex-1 items-center gap-2 px-3">
        <SidebarTrigger />
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4"
        />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbPage className="line-clamp-1">
                {getPageTitle(pathname || "")}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      <div className="ml-auto px-3">
        <NavActions />
      </div>
    </header>
  );
}