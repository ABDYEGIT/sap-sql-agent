// ══════════════════════════════════════════════════════════════════
// Yorglass IK Chatbot - React Entegrasyon Ornegi
// ══════════════════════════════════════════════════════════════════
// Bu dosya ornek/referans icindir. Kendi portaliniza uyarlayin.
//
// Kullanim:
//   const { sendMessage, response, loading } = useChatbot();
//   sendMessage("Yillik izin hakkim kac gun?");
// ══════════════════════════════════════════════════════════════════

import { useState, useCallback } from "react";

// API adresi - sunucunuzun IP/domain'i ile degistirin
const API_URL = "http://localhost:8000";

// API Guvenlik Anahtari - .env'deki API_SECRET_KEY ile ayni olmali
const API_KEY = "VWLzgNt3HNC3MjckuCfY9kSUCtNdPEgchsMF8wz3nRE";

// ──────────────────────────────────────────────────────────────────
// YONTEM 1: Custom Hook (onerilen)
// ──────────────────────────────────────────────────────────────────

export function useChatbot() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);

  const sendMessage = useCallback(
    async (message) => {
      setLoading(true);
      setError(null);

      try {
        const res = await fetch(`${API_URL}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
          body: JSON.stringify({
            message: message,
            chat_history: chatHistory,
          }),
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Sunucu hatasi");
        }

        const data = await res.json();

        // Chat gecmisini guncelle (sonraki sorular icin baglam saglar)
        setChatHistory((prev) => [
          ...prev,
          { role: "user", content: message },
          { role: "assistant", content: data.response },
        ]);

        setResponse(data);
        return data;
      } catch (err) {
        setError(err.message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [chatHistory]
  );

  // Sohbeti sifirla
  const resetChat = useCallback(() => {
    setChatHistory([]);
    setResponse(null);
    setError(null);
  }, []);

  return { sendMessage, response, loading, error, chatHistory, resetChat };
}

// ──────────────────────────────────────────────────────────────────
// YONTEM 2: Tek fonksiyon (en basit)
// ──────────────────────────────────────────────────────────────────

export async function askIKBot(message, chatHistory = []) {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
    body: JSON.stringify({
      message: message,
      chat_history: chatHistory,
    }),
  });

  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Sunucu hatasi");
  }

  return await res.json();

  // Donen veri formati:
  // {
  //   response: "Yillik izin hakkiniz...",
  //   sources: [{ section_title: "...", source_file: "...", score: 0.89 }],
  //   tokens: { input: 850, output: 320, total: 1170 }
  // }
}

// ──────────────────────────────────────────────────────────────────
// KULLANIM ORNEGI
// ──────────────────────────────────────────────────────────────────

/*
// Ornek 1: Hook ile
function MyComponent() {
  const { sendMessage, response, loading, error } = useChatbot();
  const [input, setInput] = useState("");

  const handleSubmit = async () => {
    const data = await sendMessage(input);
    console.log("Yanit:", data.response);
    console.log("Kaynaklar:", data.sources);
    setInput("");
  };

  return (
    <div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Yanitlaniyor..." : "Gonder"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {response && <p>{response.response}</p>}
    </div>
  );
}

// Ornek 2: Tek fonksiyon ile (degiskende tutma)
async function handleUserInput(userMessage) {
  try {
    const data = await askIKBot(userMessage);

    const botResponse = data.response;     // LLM yaniti
    const sources = data.sources;           // Kaynak dokumanlar
    const tokens = data.tokens;             // Token kullanimi

    // Yanitini istedigin yere yaz
    console.log(botResponse);
  } catch (err) {
    console.error("Hata:", err.message);
  }
}
*/
