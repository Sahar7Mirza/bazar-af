import {
  Apple, Ban, Bell, BellRing, BrickWall, Calendar, Carrot, CheckCircle2, CookingPot, FolderOpen, Gem, Heart, Lock, Map, Nut, Package, PackageCheck, PackageX,
  Palette, Search, ShoppingBag, ShoppingCart, Shirt, Smartphone, Sparkles, Store, Tag, TriangleAlert, Users, Wheat, ScrollText, TrendingDown, TrendingUp, Minus, Trophy, Wallet, type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  bell: Bell, "bell-ring": BellRing, cart: ShoppingCart, bag: ShoppingBag, search: Search, package: Package, "package-check": PackageCheck, "package-x": PackageX,
  store: Store, users: Users, audit: ScrollText, calendar: Calendar, map: Map, tag: Tag, phone: Smartphone, alert: TriangleAlert, lock: Lock, ban: Ban,
  "trend-up": TrendingUp, "trend-down": TrendingDown, flat: Minus, trophy: Trophy, wallet: Wallet, folder: FolderOpen, heart: Heart, sparkles: Sparkles, check: CheckCircle2,
  bakery: Wheat, produce: Carrot, nuts: Nut, textiles: Shirt, electronics: Smartphone, home: CookingPot, construction: BrickWall, handicrafts: Palette, fruit: Apple, gem: Gem,
};

/** Line icon from the Lucide set. Decorative by default (hidden from screen readers); pass `label` when the icon stands alone. */
export function Icon({ name, size = 20, label, className }: { name: string; size?: number; label?: string; className?: string }) {
  const C = ICONS[name] ?? ShoppingBag;
  return <C size={size} strokeWidth={1.75} className={className} aria-hidden={label ? undefined : true} aria-label={label} role={label ? "img" : undefined} />;
}

const CATEGORY: [RegExp, string][] = [[/bakery|food/i, "bakery"], [/produce/i, "produce"], [/dry|nut/i, "nuts"], [/textile|cloth/i, "textiles"], [/electronic|phone/i, "electronics"], [/home|kitchen/i, "home"], [/construction/i, "construction"], [/handicraft|carpet/i, "handicrafts"]];
export const categoryIcon = (name?: string | null) => CATEGORY.find(([r]) => name && r.test(name))?.[1] ?? "bag";
