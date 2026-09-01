const JSON_HEADERS = {
  "Content-Type": "application/json",
};

function authHeaders(token) {
  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {};
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "请求失败");
  }
  return data;
}

export async function registerUser(payload) {
  const response = await fetch("/auth/register", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(payload),
  });
  return parseResponse(response);
}

export async function loginUser(username, password) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });
  return parseResponse(response);
}

export async function fetchCurrentUser(token) {
  const response = await fetch("/auth/me", {
    headers: authHeaders(token),
  });
  return parseResponse(response);
}

export async function fetchDocuments() {
  const response = await fetch("/documents");
  return parseResponse(response);
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/documents/upload", {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function fetchChatSessions(mode, token) {
  const response = await fetch(`/chat/sessions?mode=${encodeURIComponent(mode)}`, {
    headers: authHeaders(token),
  });
  return parseResponse(response);
}

export async function createChatSession(mode, token, title = "") {
  const response = await fetch("/chat/sessions", {
    method: "POST",
    headers: {
      ...JSON_HEADERS,
      ...authHeaders(token),
    },
    body: JSON.stringify({ mode, title: title || null }),
  });
  return parseResponse(response);
}

export async function deleteChatSession(sessionId, token) {
  const response = await fetch(`/chat/sessions/${sessionId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  return parseResponse(response);
}

export async function fetchChatMessages(sessionId, token) {
  const response = await fetch(`/chat/sessions/${sessionId}/messages`, {
    headers: authHeaders(token),
  });
  return parseResponse(response);
}

export function streamQuestion(sessionId, payload, token, onMeta, onToken, onDone) {
  return new Promise((resolve, reject) => {
    fetch(`/chat/sessions/${sessionId}/stream`, {
      method: "POST",
      headers: {
        ...JSON_HEADERS,
        ...authHeaders(token),
      },
      body: JSON.stringify(payload),
    }).then(async (response) => {
      if (!response.ok || !response.body) {
        const data = await response.json().catch(() => ({}));
        reject(new Error(data.detail || "请求失败"));
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      const read = async () => {
        const { done, value } = await reader.read();
        if (done) {
          onDone?.();
          resolve();
          return;
        }

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const lines = part.split("\n");
          let eventName = "";
          let dataLine = "";
          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventName = line.slice(6).trim();
            }
            if (line.startsWith("data:")) {
              dataLine = line.slice(5).trim();
            }
          }

          if (eventName === "meta") {
            onMeta?.(JSON.parse(dataLine));
          } else if (eventName === "token") {
            onToken?.(JSON.parse(dataLine).text);
          } else if (eventName === "done") {
            onDone?.();
            resolve();
            return;
          }
        }

        read();
      };

      read().catch(reject);
    }).catch(reject);
  });
}
