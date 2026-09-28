import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import * as api from "../api";
import type { ChatProductCard } from "../api";
import { useAuth } from "../auth";
import { useChatResults } from "../chatResults";
import BoolaAvatar from "./BoolaAvatar";
import "./ChatPanel.css";

const MAX_INLINE_PRODUCTS = 4;

const GREETING: Message = {
  role: "assistant",
  content: "Hey, I'm Boola! 🐾 Ask me anything about our Yale gear — hoodies, sizes, prices, whatever you need.",
};

const SUGGESTED_QUESTIONS = [
  "What hoodies do you have?",
  "What's in stock in medium?",
  "Show me crewnecks under $60",
  "Where's your store located?",
];

interface Message {
  role: "user" | "assistant";
  content: string;
  products?: ChatProductCard[];
}

// The agent writes plain-text replies with occasional **bold** for emphasis
// (e.g. product names). Render that inline instead of showing literal asterisks.
function renderWithBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={i}>{part}</span>
    ),
  );
}

// The product page's id is right there in the URL, so page context can be
// derived without any cross-component state.
function currentPageContext(pathname: string): api.PageContext {
  const match = pathname.match(/^\/products\/([^/]+)$/);
  return { path: pathname, product_id: match ? decodeURIComponent(match[1]) : null };
}

export default function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>([GREETING]);
  const { setResults } = useChatResults();
  const location = useLocation();
  const navigate = useNavigate();
  const { user, token, ready } = useAuth();
  const loadedForUserId = useRef<number | null>(null);

  useEffect(() => {
    if (!ready) return;

    if (user && token) {
      if (loadedForUserId.current !== user.id) {
        loadedForUserId.current = user.id;
        api
          .fetchChatHistory(token)
          .then((history) => {
            if (history.length > 0) {
              setMessages(history);
            }
          })
          .catch(() => {});
      }
    } else if (loadedForUserId.current !== null) {
      // Was logged in, now logged out (or session expired) — clear the panel.
      loadedForUserId.current = null;
      setMessages([GREETING]);
    }
  }, [user, token, ready]);

  const hasSentMessage = messages.some((m) => m.role === "user");

  const sendMessage = async (override?: string) => {
    const text = (override ?? input).trim();
    if (!text || sending) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setSending(true);
    try {
      const reply = await api.sendChatMessage(text, currentPageContext(location.pathname), token);
      setMessages((prev) => [...prev, { role: "assistant", content: reply.reply, products: reply.products }]);
      if (reply.search_query) {
        setResults(reply.search_query, reply.products);
        if (location.pathname !== "/products") {
          navigate("/products");
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Ugh, I'm having trouble connecting right now — mind trying again?" },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-header-identity">
              <BoolaAvatar size={30} />
              <div>
                <div className="chat-header-name">Boola</div>
                <div className="chat-header-sub">Campus Customs chat buddy</div>
              </div>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => {
              const products = m.products ?? [];
              const overflow = products.length - MAX_INLINE_PRODUCTS;
              return (
                <div key={i} className={`chat-row chat-row-${m.role}`}>
                  {m.role === "assistant" && (
                    <div className="chat-avatar">
                      <BoolaAvatar size={22} />
                    </div>
                  )}
                  <div className={`chat-bubble chat-bubble-${m.role}`}>
                    <div className="chat-bubble-text">{renderWithBold(m.content)}</div>
                    {products.length > 0 && (
                      <div className="chat-products">
                        {products.slice(0, MAX_INLINE_PRODUCTS).map((p) => (
                          <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product-card">
                            <img src={p.image_url} alt={p.name} />
                            <div>
                              <div className="chat-product-name">{p.name}</div>
                              <div className="chat-product-price">${p.price.toFixed(2)}</div>
                            </div>
                          </Link>
                        ))}
                        {overflow > 0 && (
                          <Link to="/products" className="chat-products-more">
                            See all {products.length} on the Products page →
                          </Link>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {sending && (
              <div className="chat-row chat-row-assistant">
                <div className="chat-avatar">
                  <BoolaAvatar size={22} />
                </div>
                <div className="chat-bubble chat-bubble-assistant chat-bubble-typing">
                  <span className="chat-typing-dot" />
                  <span className="chat-typing-dot" />
                  <span className="chat-typing-dot" />
                </div>
              </div>
            )}
          </div>
          {!hasSentMessage && !sending && (
            <div className="chat-suggestions">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button key={q} className="chat-suggestion" onClick={() => sendMessage(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}
          <div className="chat-input-row">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Text Boola..."
              disabled={sending}
            />
            <button onClick={() => sendMessage()} disabled={sending}>
              Send
            </button>
          </div>
        </div>
      )}
      <button className="chat-fab" onClick={() => setOpen((o) => !o)} aria-label="Toggle chat">
        {open ? "×" : <BoolaAvatar size={40} />}
      </button>
    </div>
  );
}
