import { createContext, useContext, useState, type ReactNode } from "react";
import type { ChatProductCard } from "./api";

interface ChatResultsState {
  query: string;
  products: ChatProductCard[];
}

interface ChatResultsValue {
  results: ChatResultsState | null;
  setResults: (query: string, products: ChatProductCard[]) => void;
  clearResults: () => void;
}

const ChatResultsContext = createContext<ChatResultsValue | null>(null);

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<ChatResultsState | null>(null);

  const setResults = (query: string, products: ChatProductCard[]) => {
    setResultsState({ query, products });
  };
  const clearResults = () => setResultsState(null);

  return (
    <ChatResultsContext.Provider value={{ results, setResults, clearResults }}>
      {children}
    </ChatResultsContext.Provider>
  );
}

export function useChatResults(): ChatResultsValue {
  const ctx = useContext(ChatResultsContext);
  if (!ctx) throw new Error("useChatResults must be used inside a ChatResultsProvider");
  return ctx;
}
