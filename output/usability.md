# Usability improvements

Four additions on top of the existing site and chat agent: two on the front end, two on the agent/backend.

## 1. Filters and sorting on the Products page

**Added:** a small toolbar above the product grid — filter by category (Hoodies, Crewnecks, Quarter-Zips, Jackets, T-Shirts, Long-Sleeves), filter to only products with a chosen size currently in stock, and sort by price (low-to-high or high-to-low). These apply on top of whatever's currently shown, including a chat search's results (e.g. filter the "hoodies" results down to ones in stock in Medium, sorted cheapest first).

**Why it helps:** a shopper browsing 27 hoodies shouldn't have to open each one to find their size, or scroll past everything twice their budget. This turns "what hoodies do you have" into "what hoodies do you have, in my size, that I can actually afford" without a second trip to the chatbot. For the business, fewer dead-end browsing sessions (someone leaving because nothing on the first page fit) is fewer abandoned visits.

**Try it:** go to the Products page, pick a category (e.g. Hoodies) and a size (e.g. M) from the toolbar, and sort by price low-to-high. Then ask the chat "what hoodies do you have?" and apply the same size filter on top of those results.

## 2. Suggested questions and a typing indicator in the chat panel

**Added:** a handful of clickable suggested questions ("What hoodies do you have?", "What's in stock in medium?", "Show me crewnecks under $60", "Where's your store located?") shown when the chat panel is opened and nothing's been asked yet, and an animated typing indicator while the agent is working on a reply.

**Why it helps:** an empty chat box is an uninviting first impression — most shoppers don't know an AI assistant can filter by price and size until they see an example. The suggestions double as a quiet product tour. The typing indicator is a small trust signal: without it, a slow model response can look like the site is frozen or broken, which is exactly when someone closes the tab.

**Try it:** open the chat panel (bottom right) without typing anything — the suggestion chips should be there. Click one and watch the animated dots appear while the agent works on its reply.

## 3. One-step multi-filter product search (`filter_products_tool`)

**Added:** a new agent tool that finds products matching category, max price, and an in-stock size all in one database query, instead of searching by category and then checking stock product-by-product. "Show me hoodies under $60 in medium" now resolves in a single tool call.

**Why it helps the shopper:** a faster, more accurate answer to the kind of specific question a real shopper actually asks ("under $60" and "in medium" together, not one at a time). **Why it helps the business:** fewer round-trips to the model per question means lower cost and latency per chat exchange, and a correct one-shot answer is less likely to end in the shopper giving up or contacting support instead.

Testing caught a real bug here: the agent naturally passed the size as `"medium"` instead of the database's code `"M"`, which matched nothing and silently returned zero results. The tool now normalizes common size words and casings to the right code before querying, so either form works.

**Try it:** ask the chat "show me hoodies under $60 in medium" — it should answer with matching products in one step, not ask a follow-up question.

## 4. Suggesting in-stock alternatives for an out-of-stock size

**Added:** when a shopper asks about a size that's out of stock, the agent now says so clearly and then also suggests 2-4 similar products (same category) that do have that size in stock, using the same new `filter_products_tool`.

**Why it helps:** "sorry, we don't have that" is a dead end that sends the shopper elsewhere; "we don't have that, but here are three similar options in your size" keeps them shopping. For the business, this converts a near-miss (right size, wrong product) into a recovered sale instead of a lost one.

Testing caught a real bug here too: the first version listed all 18 matching alternatives instead of a curated few, which would have buried the reply and cluttered the chat panel. The prompt was tightened to suggest 2-4 rather than dumping every match.

**Try it:** ask the chat "do you have the Baseball Left Chest Crewneck in XS?" — it's out of stock in that size, so the agent should say so plainly and then suggest a small handful of similar crewnecks that do have XS in stock.
