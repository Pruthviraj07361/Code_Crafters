async function loadStudentMeeting() {
  const feed = document.getElementById("student-meeting-feed");
  const token = sessionStorage.getItem("authToken");
  feed.textContent = "Loading meetings...";
  if (!token) {
    feed.textContent = "Sign in to load meetings.";
    const nextMeeting = document.getElementById("metric-next-meeting");
    if (nextMeeting) nextMeeting.textContent = "Sign in to view meetings";
    return;
  }

  try {
    const response = await fetch("/api/student/meeting", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const meeting = await response.json();
    if (response.status === 404) {
      feed.textContent = "No meetings scheduled.";
      const nextMeeting = document.getElementById("metric-next-meeting");
      if (nextMeeting) nextMeeting.textContent = "No upcoming meetings";
      return;
    }
    if (!response.ok)
      throw new Error(meeting.detail || "Unable to load meetings.");

    const card = document.createElement("article");
    const nextMeeting = document.getElementById("metric-next-meeting");
    if (nextMeeting) {
      nextMeeting.textContent = `Next: ${new Date(
        meeting.scheduled_for,
      ).toLocaleString()}`;
    }
    card.className =
      "bg-slate-900/60 border border-white/10 backdrop-blur-xl shadow-2xl rounded-lg p-space-md flex flex-col space-y-space-xs";
    const title = document.createElement("h3");
    title.className = "font-headline-sm text-headline-sm text-white";
    title.textContent = meeting.title;
    const scheduledFor = document.createElement("p");
    scheduledFor.className = "font-body-sm text-body-sm text-slate-300";
    scheduledFor.textContent = new Date(meeting.scheduled_for).toLocaleString();
    card.append(title, scheduledFor);
    if (meeting.notes) {
      const notes = document.createElement("p");
      notes.className =
        "font-body-sm text-body-sm text-slate-300 pt-1 border-t border-white/10";
      notes.textContent = meeting.notes;
      card.append(notes);
    }
    feed.replaceChildren(card);
  } catch (error) {
    feed.textContent = error.message || "Unable to load meetings.";
    const nextMeeting = document.getElementById("metric-next-meeting");
    if (nextMeeting) nextMeeting.textContent = "Unable to load meetings";
  }
}

loadStudentMeeting();

async function loadCurrentUser() {
  const token = sessionStorage.getItem("authToken");
  if (!token) return;

  try {
    const response = await fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const user = await response.json();
    if (!response.ok) throw new Error(user.detail || "Unable to load profile.");

    const profileHeading = document.querySelector("#view-profile h1");
    const profileInitials = document.querySelector(
      "#view-profile .rounded-full",
    );
    const profileMeta = document.querySelector(
      "#view-profile .font-code-inline",
    );
    const profileBranch = profileMeta?.nextElementSibling?.nextElementSibling;
    if (profileHeading) profileHeading.textContent = user.name;
    if (profileInitials) {
      profileInitials.textContent = user.name
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join("")
        .toUpperCase();
    }
    if (profileMeta) {
      profileMeta.textContent = `Enrollment: ${user.enrollment_number}`;
    }
    if (profileBranch) profileBranch.textContent = user.branch;
    const profileEnrollment = document.getElementById("profile-enrollment");
    if (profileEnrollment) {
      profileEnrollment.textContent = `Enrollment: ${user.enrollment_number}`;
    }
    const profileBranchLabel = document.getElementById("profile-branch");
    if (profileBranchLabel) profileBranchLabel.textContent = user.branch;
    const profileEmail = document.getElementById("prof-email");
    const profileDivision = document.getElementById("prof-division");
    const profileRollNumber = document.getElementById("prof-division-roll-number");
    const profileSemester = document.getElementById("prof-semester");
    if (profileEmail) profileEmail.value = user.email || "";
    if (profileDivision) profileDivision.value = user.division || "";
    if (profileRollNumber) profileRollNumber.value = user.division_roll_number || "";
    if (profileSemester) profileSemester.value = user.semester || "";
    const cohort = document.getElementById("profile-cohort-text");
    if (cohort) {
      cohort.textContent =
        [
          user.semester ? `Semester ${user.semester}` : null,
          user.division ? `Division ${user.division}` : null,
        ]
          .filter(Boolean)
          .join(" • ") || "Not configured";
    }
  } catch (error) {
    const profileHeading = document.querySelector("#view-profile h1");
    if (profileHeading) {
      profileHeading.textContent = error.message || "Unable to load profile.";
    }
  }
}

loadCurrentUser();

window.cohortState = {
  year: "Not configured",
  sem: "Not configured",
  div: "Not configured",
};

const profileActivity = document.querySelector(
  "#view-profile .space-y-space-xs.font-body-sm",
);
if (profileActivity) {
  const emptyActivity = document.createElement("p");
  emptyActivity.className = "py-8 text-center text-sm text-slate-400";
  emptyActivity.textContent = "No submission activity is available yet.";
  profileActivity.replaceChildren(emptyActivity);
}

const profileMetrics = document.querySelector(
  "#view-profile section .flex.flex-wrap.items-center.gap-space-xs",
);
if (profileMetrics) {
  profileMetrics.replaceChildren();
  const metricsMessage = document.createElement("span");
  metricsMessage.className = "text-slate-400";
  metricsMessage.textContent =
    "Live profile metrics will appear after activity is recorded.";
  profileMetrics.append(metricsMessage);
}

function toggleCohortDropdown(type) {
  var types = ["year", "sem", "div"];
  var targetMenu = document.getElementById("menu-cohort-" + type);
  var targetIcon = document.getElementById("icon-cohort-" + type);
  var willOpen = targetMenu && targetMenu.classList.contains("hidden");

  types.forEach(function (t) {
    var m = document.getElementById("menu-cohort-" + t);
    var icon = document.getElementById("icon-cohort-" + t);
    if (m) m.classList.add("hidden");
    if (icon) icon.textContent = "expand_more";
  });

  if (willOpen && targetMenu) {
    targetMenu.classList.remove("hidden");
    if (targetIcon) targetIcon.textContent = "expand_less";
  }
}

function selectCohortOption(type, value) {
  window.cohortState[type] = value;
  var label = document.getElementById("selected-cohort-" + type);
  if (label) label.textContent = value;
  var menu = document.getElementById("menu-cohort-" + type);
  if (menu) menu.classList.add("hidden");
  var icon = document.getElementById("icon-cohort-" + type);
  if (icon) icon.textContent = "expand_more";

  updateCohortSummary();
}

function getCohortPreviewText() {
  var y = window.cohortState.year;
  var s = window.cohortState.sem === "Odd Semester" ? "Odd Sem" : "Even Sem";
  var d = window.cohortState.div.replace("Division ", "Div ");
  return y + " • " + s + " • " + d;
}

function updateCohortSummary() {
  var display = document.getElementById("cohort-status-display");
  if (display) display.textContent = getCohortPreviewText();

  var profCohort = document.getElementById("profile-cohort-text");
  if (profCohort)
    profCohort.textContent =
      window.cohortState.year +
      " • " +
      window.cohortState.sem +
      " • " +
      window.cohortState.div;
}

function saveCohortCustom() {
  updateCohortSummary();
  var toast = document.getElementById("cohort-toast-msg");
  var saveBtn = document.getElementById("cohort-save-btn");
  var saveText = document.getElementById("cohort-save-text");
  var saveIcon = document.getElementById("cohort-save-icon");

  if (saveText) saveText.textContent = "Updated!";
  if (saveIcon) saveIcon.textContent = "done";
  if (saveBtn) {
    saveBtn.classList.remove("bg-white");
    saveBtn.classList.add("bg-slate-400");
  }
  if (toast) toast.classList.remove("hidden");

  setTimeout(function () {
    if (saveText) saveText.textContent = "Update Cohort";
    if (saveIcon) saveIcon.textContent = "save";
    if (saveBtn) {
      saveBtn.classList.add("bg-white");
      saveBtn.classList.remove("bg-slate-400");
    }
    if (toast) toast.classList.add("hidden");
  }, 2000);
}

document.addEventListener("click", function (e) {
  var form = document.getElementById("cohort-form");
  if (form && !form.contains(e.target)) {
    ["year", "sem", "div"].forEach(function (t) {
      var m = document.getElementById("menu-cohort-" + t);
      var icon = document.getElementById("icon-cohort-" + t);
      if (m) m.classList.add("hidden");
      if (icon) icon.textContent = "expand_more";
    });
  }
});

// View switching logic
function switchView(viewName) {
  const views = ["challenges", "projects", "profile"];

  views.forEach((v) => {
    const el = document.getElementById("view-" + v);
    const navEl = document.getElementById("nav-" + v);

    if (el) {
      if (v === viewName) {
        el.classList.remove("hidden");
        el.classList.add("flex");
      } else {
        el.classList.add("hidden");
        el.classList.remove("flex");
      }
    }

    if (navEl) {
      if (v === viewName) {
        navEl.setAttribute("aria-current", "page");
        navEl.classList.remove("text-slate-300", "border-transparent");
        navEl.classList.add("text-white", "border-white/40", "font-medium");
      } else {
        navEl.removeAttribute("aria-current");
        navEl.classList.add("text-slate-300", "border-transparent");
        navEl.classList.remove("text-white", "border-white/40", "font-medium");
      }
    }
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Profile settings save toast
async function saveProfileSettings() {
  const toast = document.getElementById("prof-toast-msg");
  const btn = document.getElementById("prof-save-btn");
  const text = document.getElementById("prof-save-text");
  const icon = document.getElementById("prof-save-icon");

  const token = sessionStorage.getItem("authToken");
  if (!token) {
    if (toast) toast.textContent = "Sign in again to update your profile.";
    if (toast) toast.classList.remove("hidden");
    return;
  }
  if (btn) btn.disabled = true;
  try {
    const response = await fetch("/api/auth/me/profile", {
      method: "PATCH",
      headers: {
        Authorization: `******`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        division: document.getElementById("prof-division")?.value.trim(),
        division_roll_number: document
          .getElementById("prof-division-roll-number")
          ?.value.trim(),
        semester: Number(document.getElementById("prof-semester")?.value) || null,
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Unable to update profile.");
    if (text) text.textContent = "Saved!";
    if (icon) icon.textContent = "done";
    if (toast) toast.classList.remove("hidden");
    if (result.semester) {
      const cohort = document.getElementById("profile-cohort-text");
      if (cohort) cohort.textContent = `Semester ${result.semester} • Division ${result.division}`;
    }
  } catch (error) {
    if (toast) toast.textContent = error.message;
    if (toast) toast.classList.remove("hidden");
  } finally {
    if (btn) btn.disabled = false;
  }

  setTimeout(function () {
    if (text) text.textContent = "Save Profile Settings";
    if (icon) icon.textContent = "save";
    if (btn) {
      btn.classList.add("bg-white");
      btn.classList.remove("bg-slate-400");
    }
    if (toast) toast.classList.add("hidden");
  }, 2200);
}
