import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface ToastMessage {
  id: number;
  text: string;
  kind: "success" | "info";
}

interface ToastContextValue {
  showToast: (text: string, kind?: "success" | "info") => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let toastId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const showToast = useCallback((text: string, kind: "success" | "info" = "success") => {
    const id = ++toastId;
    setMessages((current) => [...current, { id, text, kind }]);
    window.setTimeout(() => {
      setMessages((current) => current.filter((message) => message.id !== id));
    }, 4000);
  }, []);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {messages.map((message) => (
          <div key={message.id} className={`toast toast-${message.kind}`} role="status">
            {message.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
