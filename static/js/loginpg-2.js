function switchToRegister() {
  const mainContainer = document.getElementById("mainContainer");
  const loginView = document.getElementById("loginView");
  const registerView = document.getElementById("registerView");

  mainContainer.classList.remove("max-w-md");
  mainContainer.classList.add("max-w-xl");

  loginView.classList.add("hidden");
  loginView.classList.remove("flex");

  registerView.classList.remove("hidden");
  registerView.classList.add("flex");
}

function switchToLogin() {
  const mainContainer = document.getElementById("mainContainer");
  const loginView = document.getElementById("loginView");
  const registerView = document.getElementById("registerView");

  mainContainer.classList.remove("max-w-xl");
  mainContainer.classList.add("max-w-md");

  registerView.classList.add("hidden");
  registerView.classList.remove("flex");

  loginView.classList.remove("hidden");
  loginView.classList.add("flex");
}

let registrationType = "student";

function setRegistrationType(type) {
  registrationType = type;
  const isStudent = type === "student";
  const studentFields = document.getElementById("student-registration-fields");
  studentFields.classList.toggle("hidden", !isStudent);
  studentFields.querySelectorAll("input, select").forEach((field) => {
    field.required = isStudent;
  });

  const labels = {
    student: ["Student Registration", "Join the campus coding club cohort."],
    faculty: [
      "Faculty Registration",
      "Faculty applications require administrator approval.",
    ],
    admin: [
      "Admin / Staff Registration",
      "An administrator will review your application and assign staff access.",
    ],
  };
  document.getElementById("register-title").textContent = labels[type][0];
  document.getElementById("register-description").textContent = labels[type][1];

  ["student", "faculty", "admin"].forEach((option) => {
    const button = document.getElementById(`register-type-${option}`);
    const selected = option === type;
    button.className = selected
      ? "flex-1 py-1.5 px-3 rounded-full text-sm text-white bg-white/15 transition-all"
      : "flex-1 py-1.5 px-3 rounded-full text-sm text-slate-400 hover:text-white transition-all";
    button.setAttribute("aria-pressed", String(selected));
  });
}

function selectRole(role) {
  const studentBtn = document.getElementById("role-student");
  const adminBtn = document.getElementById("role-admin");
  const emailInput = document.getElementById("email");

  if (role === "student") {
    studentBtn.className =
      "flex-1 py-1.5 px-4 rounded-full text-base text-white bg-white/15 shadow-sm transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer";
    studentBtn.setAttribute("aria-selected", "true");
    adminBtn.className =
      "flex-1 py-1.5 px-4 rounded-full text-base text-slate-400 hover:text-white bg-transparent transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer";
    adminBtn.setAttribute("aria-selected", "false");
    emailInput.placeholder = "alex@university.edu";
  } else {
    adminBtn.className =
      "flex-1 py-1.5 px-4 rounded-full text-base text-white bg-white/15 shadow-sm transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer";
    adminBtn.setAttribute("aria-selected", "true");
    studentBtn.className =
      "flex-1 py-1.5 px-4 rounded-full text-base text-slate-400 hover:text-white bg-transparent transition-all duration-150 flex items-center justify-center gap-1.5 cursor-pointer";
    studentBtn.setAttribute("aria-selected", "false");
    emailInput.placeholder = "lead@codingclub.ac.uk";
  }
}

function togglePasswordVisibility() {
  const pwd = document.getElementById("password");
  const icon = document.getElementById("passwordToggleIcon");
  if (pwd.type === "password") {
    pwd.type = "text";
    icon.textContent = "visibility_off";
  } else {
    pwd.type = "password";
    icon.textContent = "visibility";
  }
}

function showFormMessage(elementId, message, isError = true) {
  const element = document.getElementById(elementId);
  element.textContent = message;
  element.classList.toggle("hidden", !message);
  element.classList.toggle("text-rose-300", isError);
  element.classList.toggle("text-emerald-300", !isError);
}

function getApiErrorMessage(data) {
  if (data.detail) return data.detail;
  return Object.values(data).flat().join(" ");
}

async function handleLoginSubmit() {
  const btn = document.getElementById("submitBtn");
  const originalContent = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span><span>Verifying...</span>`;
  showFormMessage("loginMessage", "");
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(getApiErrorMessage(data));

    sessionStorage.setItem("authToken", data.token);
    sessionStorage.setItem("authUser", JSON.stringify(data.user));
    const destinations = {
      student: "/preview/student/",
      faculty: "/preview/faculty/",
      supervisor: "/preview/supervisor/",
      superuser: "/preview/supervisor/",
    };
    window.location.assign(destinations[data.user.role] || "/preview/");
  } catch (error) {
    showFormMessage(
      "loginMessage",
      error.message || "Unable to sign in. Please try again.",
    );
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalContent;
  }
}

async function handleRegisterSubmit() {
  const btn = document.getElementById("registerSubmitBtn");
  const originalContent = btn.innerHTML;
  const password = document.getElementById("reg-password").value;
  if (password !== document.getElementById("reg-password-confirm").value) {
    showFormMessage("registerMessage", "Passwords do not match.");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = `<span class="material-symbols-outlined text-[16px] animate-spin">progress_activity</span><span>Submitting application...</span>`;
  showFormMessage("registerMessage", "");
  try {
    const payload = {
      name: document.getElementById("reg-fullname").value,
      email: document.getElementById("reg-gmail").value,
      phone: document.getElementById("reg-phone").value,
      password,
    };
    let endpoint = "/api/auth/admin/register";
    if (registrationType === "student") {
      endpoint = "/api/auth/student/register";
      Object.assign(payload, {
        enrollment_number: document.getElementById("reg-enrollment").value,
        division_roll_number: document.getElementById("reg-roll").value,
        branch: document.getElementById("reg-branch").value,
        division: document.getElementById("reg-division").value,
      });
    } else {
      payload.requested_role = registrationType === "faculty" ? "faculty" : "";
    }

    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(getApiErrorMessage(data));

    document.querySelector("#registerView form").reset();
    showFormMessage("registerMessage", data.detail, false);
  } catch (error) {
    showFormMessage(
      "registerMessage",
      error.message || "Unable to register. Please try again.",
    );
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalContent;
  }
}
