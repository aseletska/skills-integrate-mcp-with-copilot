document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const loginForm = document.getElementById("login-form");
  const logoutBtn = document.getElementById("logout-btn");
  const authStatus = document.getElementById("auth-status");
  const emailInput = document.getElementById("email");
  const usernameInput = document.getElementById("username");
  const passwordInput = document.getElementById("password");
  const messageDiv = document.getElementById("message");

  let authToken = localStorage.getItem("authToken") || "";
  let currentUser = null;

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = type;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  function authHeaders() {
    return authToken ? { "X-Auth-Token": authToken } : {};
  }

  function updateAuthUi() {
    if (!currentUser) {
      authStatus.textContent = "Not signed in";
      emailInput.value = "";
      emailInput.removeAttribute("readonly");
      return;
    }

    authStatus.textContent = `Signed in as ${currentUser.username} (${currentUser.role})`;
    if (currentUser.role === "student") {
      emailInput.value = currentUser.email;
      emailInput.setAttribute("readonly", "readonly");
    } else {
      emailInput.removeAttribute("readonly");
    }
  }

  async function restoreSession() {
    if (!authToken) {
      updateAuthUi();
      return;
    }

    try {
      const response = await fetch("/auth/me", { headers: authHeaders() });
      if (!response.ok) {
        throw new Error("Session is no longer valid");
      }

      currentUser = await response.json();
      updateAuthUi();
    } catch (error) {
      authToken = "";
      currentUser = null;
      localStorage.removeItem("authToken");
      updateAuthUi();
    }
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) =>
                      `<li><span class="participant-email">${email}</span><button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button></li>`
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    if (!authToken) {
      showMessage("Please sign in first.", "error");
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: authHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: usernameInput.value,
          password: passwordInput.value,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        showMessage(result.detail || "Login failed", "error");
        return;
      }

      authToken = result.token;
      currentUser = result.user;
      localStorage.setItem("authToken", authToken);
      passwordInput.value = "";
      updateAuthUi();
      showMessage("Signed in successfully.", "success");
    } catch (error) {
      showMessage("Could not sign in. Please try again.", "error");
      console.error("Error signing in:", error);
    }
  });

  logoutBtn.addEventListener("click", () => {
    authToken = "";
    currentUser = null;
    localStorage.removeItem("authToken");
    loginForm.reset();
    updateAuthUi();
    showMessage("You have been signed out.", "info");
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!authToken) {
      showMessage("Please sign in first.", "error");
      return;
    }

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
          headers: authHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(result.message, "success");
        signupForm.reset();
        if (currentUser && currentUser.role === "student") {
          emailInput.value = currentUser.email;
        }

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        showMessage(result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage("Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  restoreSession();
  fetchActivities();
});
