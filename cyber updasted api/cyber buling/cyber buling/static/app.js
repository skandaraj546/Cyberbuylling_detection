// DOM Elements
const $ = (q) => document.querySelector(q);
const messagesEl = $("#messages");
const warningsEl = $("#warnings");
const usernameEl = $("#username");
const messageInput = $("#messageInput");
const fileInput = $("#fileInput");
const postBtn = $("#postBtn");
const refreshBtn = $("#refreshBtn");
const template = $("#messageTemplate");

// State
let messages = [];
let isPosting = false;
let refreshInterval;
let socket = null;

// Initialize WebSocket connection
function initWebSocket() {
  try {
    // Try to connect to SocketIO
    if (typeof io !== 'undefined') {
      socket = io();

      socket.on('connect', () => {
        console.log('Connected to CyberGuard');
        showNotification('Connected to real-time feed', 'success');
      });

      socket.on('disconnect', () => {
        console.log('Disconnected from CyberGuard');
        showNotification('Connection lost. Trying to reconnect...', 'error');
      });

      socket.on('new_message', (messageData) => {
        // Add new message to feed
        messages.push(messageData);
        renderMessages(messages);

        // Show notification for new posts
        if (!messageData.bot) {
          showNotification(`New post from ${messageData.username}`, 'info');
        }
      });

      socket.on('feed_update', (data) => {
        if (data.messages) {
          messages = data.messages;
          renderMessages(messages);
        }
      });

      // Join the feed
      socket.emit('join_feed');
    }
  } catch (error) {
    console.log('WebSocket not available, using polling fallback');
  }
}

// Utility Functions
function formatTime(iso) {
  try {
    const date = new Date(iso);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "now";
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    return date.toLocaleDateString();
  } catch {
    return "";
  }
}

function createToxicityChips(labels, scores) {
  const frag = document.createDocumentFragment();
  if (!labels || labels.length === 0) return frag;

  labels.forEach((label) => {
    const span = document.createElement("span");
    span.className = "chip";
    span.textContent = label;
    if (scores && scores[label]) {
      span.title = `Confidence: ${Math.round(scores[label] * 100)}%`;
    }
    frag.appendChild(span);
  });
  return frag;
}

function createMessageItem(msg) {
  const node = template.content.firstElementChild.cloneNode(true);
  node.dataset.id = msg.id || "";

  // Set user info
  node.querySelector(".username").textContent = msg.username || "Anonymous";
  node.querySelector(".timestamp").textContent = formatTime(msg.timestamp);

  // Set content
  const textContent = node.querySelector(".text-content");
  const imageContent = node.querySelector(".image-content");
  const toxicityIndicators = node.querySelector(".toxicity-indicators");

  if (msg.type === "image") {
    // Handle image content
    const wrapper = document.createElement("div");
    wrapper.className = "image-wrapper";

    const img = document.createElement("img");
    img.src = msg.image_url;
    img.alt = "uploaded image";
    img.className = "chat-image" + (msg.status === "blur" ? " blurred" : "");
    wrapper.appendChild(img);

    if (msg.status === "blur") {
      const overlay = document.createElement("div");
      overlay.className = "blur-overlay";
      overlay.innerHTML = `
        <div style="text-align: center;">
          <i class="fas fa-eye-slash" style="font-size: 24px; margin-bottom: 8px;"></i>
          <div>Content blurred for safety</div>
          <button class="reveal-btn" style="margin-top: 8px; padding: 8px 16px; background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); border-radius: 20px; color: white; cursor: pointer;">Reveal</button>
        </div>
      `;
      wrapper.appendChild(overlay);

      // Add reveal functionality
      const revealBtn = overlay.querySelector(".reveal-btn");
      revealBtn.addEventListener("click", () => {
        img.classList.remove("blurred");
        overlay.remove();
      });
    }

    imageContent.appendChild(wrapper);

    // Add extracted text if available
    if (msg.extracted_text) {
      const textDiv = document.createElement("div");
      textDiv.style.marginTop = "8px";
      textDiv.style.fontSize = "12px";
      textDiv.style.color = "rgba(255,255,255,0.6)";
      textDiv.textContent = `Extracted text: ${msg.extracted_text}`;
      imageContent.appendChild(textDiv);
    }
  } else {
    // Handle text content
    if (msg.status === "block") {
      textContent.innerHTML = `
        <div style="color: #ff6b6b; font-style: italic;">
          <i class="fas fa-ban"></i> Message blocked due to toxic content
        </div>
        <div style="margin-top: 8px; opacity: 0.7;">
          ${msg.masked_message || "**"}
        </div>
      `;
    } else {
      textContent.textContent = msg.message;
    }
  }

  // Add toxicity indicators
  console.log("Message toxicity data:", { labels: msg.labels, scores: msg.scores, status: msg.status });
  if (msg.labels && msg.labels.length > 0) {
    toxicityIndicators.appendChild(createToxicityChips(msg.labels, msg.scores));
  }

  // Handle bot messages
  if (msg.bot) {
    node.classList.add("bot-message");
    node.style.borderLeft = "3px solid #00d4ff";
  }

  // Add report functionality
  const reportBtn = node.querySelector(".report-btn");
  reportBtn.addEventListener("click", async () => {
    const reason = prompt("Why are you reporting this content?") || "";
    if (reason.trim()) {
      try {
        await fetch("/api/report", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: msg.id, reason })
        });
        showNotification("Report submitted successfully", "success");
      } catch (e) {
        showNotification("Failed to submit report", "error");
      }
    }
  });

  // Add like functionality
  const likeBtn = node.querySelector(".like-btn");
  likeBtn.addEventListener("click", () => {
    const countSpan = likeBtn.querySelector(".count");
    const currentCount = parseInt(countSpan.textContent) || 0;
    if (likeBtn.classList.contains("liked")) {
      likeBtn.classList.remove("liked");
      likeBtn.querySelector("i").className = "far fa-heart";
      countSpan.textContent = currentCount - 1;
    } else {
      likeBtn.classList.add("liked");
      likeBtn.querySelector("i").className = "fas fa-heart";
      countSpan.textContent = currentCount + 1;
    }
  });

  return node;
}

function renderMessages(list) {
  messagesEl.innerHTML = "";
  list.forEach((m) => messagesEl.appendChild(createMessageItem(m)));
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showNotification(message, type = "info") {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: ${type === "success" ? "rgba(0, 212, 255, 0.9)" : type === "error" ? "rgba(255, 107, 107, 0.9)" : "rgba(255, 255, 255, 0.9)"};
    color: ${type === "info" ? "#333" : "white"};
    border-radius: 12px;
    backdrop-filter: blur(20px);
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s ease-out";
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function updatePostButton() {
  const hasUsername = usernameEl.value.trim().length > 0;
  const hasMessage = messageInput.value.trim().length > 0;
  postBtn.disabled = !hasUsername || !hasMessage || isPosting;

  if (isPosting) {
    postBtn.textContent = "Posting...";
  } else {
    postBtn.textContent = "Post";
  }
}

async function loadMessages() {
  try {
    const res = await fetch("/api/messages");
    const data = await res.json();
    if (data.ok && Array.isArray(data.messages)) {
      messages = data.messages;
      renderMessages(messages);
    }
  } catch (e) {
    console.error("Failed to load messages:", e);
  }
}

async function postMessage() {
  if (isPosting) return;

  const username = usernameEl.value.trim() || "Anonymous";
  const text = messageInput.value.trim();
  const postToTwitter = document.getElementById('postToTwitter')?.checked || false;

  if (!text) return;

  isPosting = true;
  updatePostButton();
  warningsEl.textContent = "";

  try {
    const requestBody = {
      username,
      message: text,
      postToTwitter: postToTwitter
    };

    const res = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody)
    });

    const data = await res.json();

    // Debug logging
    console.log("Post response:", data);

    if (!data.ok) {
      warningsEl.textContent = data.error || "Failed to post message";
      return;
    }

    if (data.status === "block") {
      warningsEl.textContent = "Message blocked due to detected toxic content";
      showNotification("Message blocked for safety", "error");

      // Add blocked message preview
      messages.push({
        id: data.id,
        type: "text",
        username,
        message: data.masked_message || "**",
        labels: data.labels,
        scores: data.scores,
        status: "blocked-preview",
        timestamp: data.timestamp,
      });
      renderMessages(messages);
    } else {
      // Add user message
      const userMsg = {
        id: data.id,
        type: "text",
        username,
        message: data.message,
        labels: data.labels,
        scores: data.scores,
        status: data.status,
        timestamp: data.timestamp,
      };
      messages.push(userMsg);

      // Add bot reply if available
      if (data.bot_message) {
        messages.push({
          id: `${data.id}-bot`,
          type: "text",
          username: data.bot_username || "CyberGuard Bot",
          message: data.bot_message,
          labels: [],
          scores: {},
          status: "ok",
          timestamp: new Date().toISOString(),
          bot: true,
        });
      }

      renderMessages(messages);
      messageInput.value = "";

      // Show success notification with Twitter feedback
      let notificationMessage = "Message posted successfully";
      if (postToTwitter) {
        if (data.twitter_posted) {
          notificationMessage += " and posted to Twitter! 🐦";
        } else {
          notificationMessage += " (Twitter posting failed)";
        }
      }
      showNotification(notificationMessage, "success");
    }
  } catch (e) {
    warningsEl.textContent = "Network error. Please try again.";
    showNotification("Failed to post message", "error");
  } finally {
    isPosting = false;
    updatePostButton();
  }
}

async function uploadImage() {
  if (!fileInput.files || fileInput.files.length === 0) return;

  const username = usernameEl.value.trim() || "Anonymous";
  const form = new FormData();
  form.append("file", fileInput.files[0]);
  form.append("username", username);

  warningsEl.textContent = "";
  
  // Show uploading indicator
  showNotification("Uploading image...", "info");

  try {
    const res = await fetch("/api/upload", { method: "POST", body: form });
    const data = await res.json();

    // Debug logging
    console.log("Upload response:", data);
    console.log("Response status:", res.status);

    // Check if response is not OK (400, 500, etc.)
    if (!res.ok || !data.ok) {
      const errorMsg = data.error || "Upload failed";
      warningsEl.textContent = "🚫 " + errorMsg;
      warningsEl.style.color = "#ff4757";
      warningsEl.style.padding = "10px";
      warningsEl.style.background = "#ffe0e0";
      warningsEl.style.borderRadius = "5px";
      
      // Show detailed error if toxic image
      if (data.labels && data.labels.length > 0) {
        warningsEl.textContent += `\nDetected: ${data.labels.join(", ")}`;
      }
      
      showNotification("❌ " + errorMsg, "error");
      fileInput.value = ""; // Clear the file input
      return;
    }

    // Success - add to messages
    messages.push({
      id: data.id,
      type: "image",
      username,
      image_url: data.image_url,
      extracted_text: data.extracted_text,
      labels: data.labels,
      scores: data.scores,
      status: data.status,
      timestamp: data.timestamp,
    });

    renderMessages(messages);
    fileInput.value = "";

    if (data.status === "blur") {
      showNotification("⚠️ Image blurred for safety", "warning");
    } else {
      showNotification("✅ Image uploaded successfully", "success");
    }
  } catch (e) {
    console.error("Upload error:", e);
    warningsEl.textContent = "❌ Network error. Please try again.";
    warningsEl.style.color = "#ff4757";
    showNotification("Failed to upload image", "error");
    fileInput.value = ""; // Clear the file input
  }
}

// Event Listeners
messageInput.addEventListener("input", updatePostButton);
usernameEl.addEventListener("input", updatePostButton);

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    postMessage();
  }
});

postBtn.addEventListener("click", postMessage);

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    uploadImage();
  }
});

refreshBtn.addEventListener("click", () => {
  refreshBtn.classList.add("loading");
  loadMessages().finally(() => {
    setTimeout(() => refreshBtn.classList.remove("loading"), 500);
  });
});

// Initialize WebSocket and start polling fallback
initWebSocket();

// Auto-refresh every 10 seconds as fallback
refreshInterval = setInterval(loadMessages, 10000);

// Initial load
loadMessages();

// Add CSS animations
const style = document.createElement("style");
style.textContent = `
  @keyframes slideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }
  
  @keyframes slideOut {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
  }
  
  .bot-message {
    background: rgba(0, 212, 255, 0.05);
    border-left: 3px solid #00d4ff;
  }
  
  .liked {
    color: #ff6b6b !important;
  }
  
  .reveal-btn:hover {
    background: rgba(255,255,255,0.3) !important;
  }
  
  .loading {
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
`;
document.head.appendChild(style);

// Test toxicity function
window.testToxicity = async function () {
  const testTexts = [
    "Hello, how are you?",
    "You are stupid and ugly",
    "I hate you so much",
    "This is a normal message",
    "You should kill yourself"
  ];

  for (const text of testTexts) {
    try {
      const response = await fetch('/api/test/toxicity', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
      });

      const result = await response.json();
      console.log(`Test: "${text}"`, result);

      if (result.ok) {
        const status = result.is_toxic ? "TOXIC" : "SAFE";
        const labels = result.labels.length > 0 ? result.labels.join(", ") : "none";
        console.log(`Result: ${status} - Labels: ${labels}`);
      }
    } catch (error) {
      console.error('Test error:', error);
    }
  }

  alert('Toxicity tests completed! Check console for results.');
};
