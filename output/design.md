# Design changes

A restyle of the whole site to feel like a real Campus Customs storefront — erudite and Yale-inspired, but young and fun — plus a shopping quiz.

## Colors

Switched to a pastel palette: cream backgrounds, a soft light Yale-blue for secondary surfaces, and one coral accent for small highlights (tape color, active nav underline). Navy stayed the color for all text and every primary button.

**Why it helps:** a Yale-toned pastel look reads as this specific store's brand rather than a generic template, while keeping navy on all functional text preserves readability and trust.

**Try it:** any page — nav bar, buttons, and body text are navy; page backgrounds and banners are cream/soft-blue.

## Fonts

Body text uses Calibri (falling back to Carlito, a metric-compatible Google Font); headings use Cormorant Garamond, a classic serif.

**Why it helps:** serif headings read as collegiate rather than generic-SaaS, while the plain body font keeps prices and descriptions easy to scan — which matters more to a purchase than first impressions do.

**Try it:** any page — compare a heading (e.g. "Products") to the body text below it.

## Collage-style product grid

Product cards get a small stable tilt, a washi-tape accent, and an occasional larger card — all deterministic per product, so they don't reshuffle on filter/sort. Filtering, sorting, and chat search results work exactly as before. Cards straighten and lift on hover.

**Why it helps:** a scattered, tactile grid invites more browsing than a uniform one, which is more time to find something worth buying.

**Try it:** Products page — tilt/tape on each card, hover to see it straighten and lift.

## Chat: Boola the bulldog

The assistant is now named Boola, after "Boola Boola," Yale's fight song, with an original hand-built SVG bulldog avatar (not Yale's mascot art), texting-style bubbles, and a warmer, casual voice in `prompts/prompt.md`. Every existing rule — tool-only prices/stock, no invented data, out-of-stock alternatives, customer identity, safety rules — is unchanged; only the personality is new, and I re-ran the behavior checks after to confirm nothing regressed.

**Why it helps:** a named, friendly presence lowers the bar to actually ask a question instead of giving up and leaving.

**Try it:** open the chat panel (bottom right) — Boola's avatar and name are in the header.

## Motion

Cards fade in on scroll, cards/buttons lift on hover, and the chat has an animated typing indicator — all gated behind `prefers-reduced-motion` in both CSS and JS, so that setting gets a fully static site, not a broken one.

**Why it helps:** subtle motion makes the site feel alive without costing usability for anyone who has motion turned off.

**Try it:** scroll the Products page normally, then toggle "reduce motion" in your OS settings and reload — animations disappear, nothing looks broken.

## "Find Your Yale Fit" quiz

A 4-question quiz ("Your ideal Saturday?", "Pick a vibe," etc.) scores the real catalogue by category, color, price tier, and how you rep Yale, then shows your top 3 real matches — real photos, prices, and product links — with confetti on the results (skipped under reduced motion). The Home page has a coral quiz button with navy text, checked for readability at about a 5.8:1 contrast ratio, which passes WCAG AA. A small popup invites people to take it once per session, after a short delay.

**Why it helps:** a shopper who doesn't know what they want yet is likely to leave empty-handed; ending in 3 concrete, clickable picks is a strong way to turn browsing into a purchase.

Testing caught a real bug: one "neutral" quiz answer was secretly biasing recommendations toward the cheapest items. Fixed so it now carries no price signal at all.

**Try it:** Home page — coral "Find Your Yale Fit" button, or wait ~6 seconds for the popup in the bottom-left corner.
