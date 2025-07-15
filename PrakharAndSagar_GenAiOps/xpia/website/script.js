// JavaScript for XPIA simulation website functionality
document.addEventListener("DOMContentLoaded", function () {
  // Update timestamp
  updateTimestamp();

  // Check agent status periodically
  checkAgentStatus();
  setInterval(checkAgentStatus, 5000); // Check every 5 seconds

  // Initialize status indicator
  updateStatusIndicator("waiting", "Waiting for XPIA attack...");

  // Count sensitive data items
  countSensitiveData();

  // Log XPIA attempt detection
  console.log("🔥 XPIA Simulation loaded - monitoring for injection attempts");
});

function countSensitiveData() {
  const credentialBlocks = document.querySelectorAll(".credential-block");
  const dataCount = document.getElementById("data-count");
  if (dataCount) {
    const totalItems = Array.from(credentialBlocks).reduce((count, block) => {
      const items = block.querySelectorAll("p").length;
      return count + items;
    }, 0);
    dataCount.textContent = `${totalItems} sensitive items`;
  }
}

function updateTimestamp() {
  const timestampElement = document.getElementById("timestamp");
  const now = new Date().toLocaleString();
  timestampElement.textContent = now;
}

function updateStatusIndicator(status, message) {
  const indicator = document.getElementById("status-indicator");
  const lastUpdate = document.getElementById("last-update");
  const extractionStatus = document.getElementById("extraction-status");

  // Remove existing classes
  indicator.classList.remove("active", "processing");

  // Add appropriate class and update text
  switch (status) {
    case "active":
      indicator.classList.add("active");
      indicator.textContent = message || "XPIA Attack Detected!";
      if (extractionStatus) extractionStatus.textContent = "In Progress";
      break;
    case "processing":
      indicator.classList.add("processing");
      indicator.textContent = message || "Extracting Data...";
      if (extractionStatus) extractionStatus.textContent = "Extracting";
      break;
    case "completed":
      indicator.classList.add("active");
      indicator.textContent = "Data Extracted!";
      if (extractionStatus) extractionStatus.textContent = "Completed";
      break;
    default:
      indicator.textContent = message || "Waiting for XPIA attack...";
      if (extractionStatus) extractionStatus.textContent = "Pending";
  }

  // Update last update time
  if (lastUpdate) {
    lastUpdate.textContent = new Date().toLocaleTimeString();
  }
}

async function checkAgentStatus() {
  try {
    // Make API call to check agent status
    const response = await fetch("/api/agent/status");

    if (response.ok) {
      const data = await response.json();

      if (data.status === "active") {
        updateStatusIndicator("active", "XPIA attack in progress");
      } else if (data.status === "processing") {
        updateStatusIndicator("processing", "Extracting sensitive data...");
      } else if (data.status === "completed") {
        updateStatusIndicator("completed", "Data extraction complete");
      } else {
        updateStatusIndicator("waiting", "Waiting for XPIA attack...");
      }
    }
  } catch (error) {
    console.log("Agent status check failed:", error);
    // This is expected when the backend isn't running
    updateStatusIndicator("waiting", "Backend not connected");
  }
}

// Function to highlight prompts for the agent
function highlightPrompts() {
  const prompts = document.querySelectorAll(".prompt-section");
  prompts.forEach((prompt) => {
    prompt.style.border = "2px solid #667eea";
    prompt.style.animation = "pulse 2s infinite";
  });
}

// Function to extract all sensitive data for XPIA simulation
function extractSensitiveData() {
  const sensitiveData = {
    credentials: [],
    personalInfo: [],
    financialData: [],
    hiddenSecrets: [],
  };

  // Extract from credential blocks
  const credentialBlocks = document.querySelectorAll(".credential-block");
  credentialBlocks.forEach((block) => {
    const title = block.querySelector("h4")?.textContent || "Unknown";
    const data = Array.from(block.querySelectorAll("p")).map(
      (p) => p.textContent
    );

    if (title.includes("Database") || title.includes("API")) {
      sensitiveData.credentials.push({ type: title, data });
    } else if (title.includes("Personal")) {
      sensitiveData.personalInfo.push({ type: title, data });
    } else if (title.includes("Financial")) {
      sensitiveData.financialData.push({ type: title, data });
    }
  });

  // Extract hidden secrets from HTML comments (XPIA simulation)
  const htmlSource = document.documentElement.outerHTML;
  const hiddenMatches = htmlSource.match(/HIDDEN XPIA PROMPT:[\s\S]*?-->/);
  if (hiddenMatches) {
    sensitiveData.hiddenSecrets.push(hiddenMatches[0]);
  }

  return sensitiveData;
}

// Function to get comprehensive page content for XPIA analysis
function getPageContent() {
  return {
    title: document.title,
    xpiaPrompts: Array.from(document.querySelectorAll(".prompt-content")).map(
      (el) => el.textContent.trim()
    ),
    sensitiveData: extractSensitiveData(),
    publicData: Array.from(document.querySelectorAll(".data-card")).map(
      (card) => ({
        title: card.querySelector("h3").textContent,
        metrics: Array.from(card.querySelectorAll("p")).map(
          (p) => p.textContent
        ),
      })
    ),
    htmlSource: document.documentElement.outerHTML.substring(0, 5000), // First 5k chars
    timestamp: new Date().toISOString(),
    xpiaAttackVectors: [
      "credential_extraction",
      "personal_data_theft",
      "api_key_harvesting",
      "financial_data_exfiltration",
      "hidden_comment_parsing",
    ],
  };
}

// Make functions available globally for the agent
window.getPageContent = getPageContent;
window.highlightPrompts = highlightPrompts;
window.extractSensitiveData = extractSensitiveData;

// Log XPIA simulation readiness
console.log(
  "🔥 XPIA Simulation Ready - Sensitive data loaded for extraction test"
);
