const MAP: [RegExp, string][] = [[/bakery|food/i, "🥖"], [/produce/i, "🍅"], [/dry|nut/i, "🌰"], [/textile|cloth/i, "🧵"], [/electronic|phone/i, "📱"], [/home|kitchen/i, "🍳"], [/construction/i, "🧱"], [/handicraft|carpet/i, "🧶"]];
export const emojiFor = (name?: string | null) => MAP.find(([r]) => name && r.test(name))?.[1] ?? "🛍️";
