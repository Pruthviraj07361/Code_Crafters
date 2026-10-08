// Dynamic Tab Navigation Controller
const progressTab = document.createElement("button");
progressTab.className =
  "nav-tab h-full flex items-center gap-2 font-label-md text-label-md hover:text-white border-b-2 transition-colors whitespace-nowrap text-slate-300 border-transparent";
progressTab.dataset.target = "progress-view";
progressTab.type = "button";
progressTab.textContent = "Student Progress";
document.getElementById("portal-nav-tabs").append(progressTab);

const progressView = document.createElement("section");
progressView.id = "progress-view";
progressView.className = "portal-view flex-col w-full hidden";
progressView.innerHTML = `
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 pt-6 pb-6">
      <div>
        <h1 class="font-headline-lg text-headline-lg text-white tracking-tight font-medium">Student Progress</h1>
        <p class="text-sm text-slate-300 mt-1" id="faculty-progress-count">Loading student progress...</p>
      </div>
      <div class="flex flex-col sm:flex-row gap-3">
        <input class="h-9 px-3 bg-slate-800/40 border border-white/10 rounded text-sm text-white placeholder:text-slate-400" id="faculty-progress-search" placeholder="Search name or enrollment..." type="search">
        <select class="h-9 px-3 bg-slate-800/40 border border-white/10 rounded text-sm text-white [&>option]:bg-slate-900" id="faculty-progress-division">
          <option value="all">All Divisions</option>
        </select>
        <button class="h-9 px-4 rounded border border-white/10 bg-white/5 text-white text-sm hover:bg-white/10" id="faculty-progress-refresh" type="button">Refresh</button>
      </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div class="bg-slate-900/60 border border-white/10 rounded-lg p-4"><div class="text-xs uppercase text-slate-400">Approved Students</div><div class="text-xl text-white mt-2" id="faculty-progress-total">Loading</div></div>
      <div class="bg-slate-900/60 border border-white/10 rounded-lg p-4"><div class="text-xs uppercase text-slate-400">Average Solved</div><div class="text-xl text-white mt-2" id="faculty-progress-average">Loading</div></div>
      <div class="bg-slate-900/60 border border-white/10 rounded-lg p-4"><div class="text-xs uppercase text-slate-400">Needs Review</div><div class="text-xl text-white mt-2" id="faculty-progress-reviews">Loading</div></div>
      <div class="bg-slate-900/60 border border-white/10 rounded-lg p-4"><div class="text-xs uppercase text-slate-400">Pass Rate</div><div class="text-xl text-white mt-2" id="faculty-progress-pass-rate">Loading</div></div>
    </div>
    <div class="w-full bg-slate-900/60 border border-white/10 rounded-lg overflow-x-auto">
      <table class="w-full text-left min-w-[760px]">
        <thead><tr class="bg-slate-800/40 text-xs uppercase text-slate-400">
          <th class="py-3 px-4">Student</th><th class="py-3 px-4">Division</th><th class="py-3 px-4">Solved / Total</th><th class="py-3 px-4">Latest Problem</th><th class="py-3 px-4">Status</th><th class="py-3 px-4">Last Submission</th>
        </tr></thead>
        <tbody class="divide-y divide-white/5 text-sm text-white" id="faculty-student-progress-body"><tr><td class="py-8 px-4 text-center text-slate-400" colspan="6">Loading student progress...</td></tr></tbody>
      </table>
    </div>`;
document.querySelector(".portal-view").parentElement.append(progressView);

const navTabs = document.querySelectorAll(".nav-tab");
const portalViews = document.querySelectorAll(".portal-view");

navTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    const targetId = tab.dataset.target;

    // Update Nav Tab Styles
    navTabs.forEach((t) => {
      t.classList.remove("text-white", "border-white/40", "font-semibold");
      t.classList.add("text-slate-300", "border-transparent");
    });
    tab.classList.remove("text-slate-300", "border-transparent");
    tab.classList.add("text-white", "border-white/40", "font-semibold");

    // Toggle Active View
    portalViews.forEach((view) => {
      if (view.id === targetId) {
        view.classList.remove("hidden");
        view.classList.add("flex");
      } else {
        view.classList.add("hidden");
        view.classList.remove("flex");
      }
    });
  });
});

const facultyProgressBody = document.getElementById(
  "faculty-student-progress-body",
);
const facultyProgressSearch = document.getElementById(
  "faculty-progress-search",
);
const facultyProgressDivision = document.getElementById(
  "faculty-progress-division",
);
let facultyProgressStudents = [];

function filterFacultyProgress() {
  const query = facultyProgressSearch.value.trim().toLowerCase();
  const selectedDivision = facultyProgressDivision.value;
  let visibleCount = 0;
  facultyProgressBody
    .querySelectorAll(".faculty-progress-row")
    .forEach((row) => {
      const matchesQuery =
        !query || row.textContent.toLowerCase().includes(query);
      const matchesDivision =
        selectedDivision === "all" || row.dataset.division === selectedDivision;
      row.hidden = !matchesQuery || !matchesDivision;
      if (!row.hidden) visibleCount += 1;
    });
  document.getElementById("faculty-progress-count").textContent =
    `Showing ${visibleCount} of ${facultyProgressStudents.length} approved students`;
}

function renderFacultyStudentProgress(data) {
  facultyProgressStudents = data.students || [];
  facultyProgressBody.replaceChildren();
  facultyProgressDivision.replaceChildren(new Option("All Divisions", "all"));
  [...new Set(facultyProgressStudents.map((student) => student.division))]
    .sort()
    .forEach((division) => {
      facultyProgressDivision.add(new Option(`Division ${division}`, division));
    });

  if (!facultyProgressStudents.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.className = "py-8 px-4 text-center text-slate-400";
    cell.colSpan = 6;
    cell.textContent = "No approved student records available.";
    row.append(cell);
    facultyProgressBody.append(row);
  }

  facultyProgressStudents.forEach((student) => {
    const row = document.createElement("tr");
    row.className = "faculty-progress-row hover:bg-slate-800/30";
    row.dataset.division = student.division;
    const identityCell = document.createElement("td");
    identityCell.className = "py-3 px-4";
    const identity = document.createElement("div");
    identity.className = "flex flex-col";
    const name = document.createElement("span");
    name.className = "font-medium";
    name.textContent = student.name;
    const enrollment = document.createElement("span");
    enrollment.className = "text-xs text-slate-400";
    enrollment.textContent = student.enrollment_number;
    identity.append(name, enrollment);
    identityCell.append(identity);
    row.append(identityCell);

    const solvedCell = document.createElement("td");
    solvedCell.className = "py-3 px-4";
    solvedCell.textContent = `${student.solved_count} / ${student.total_count}`;
    const latestCell = document.createElement("td");
    latestCell.className = "py-3 px-4";
    latestCell.textContent =
      student.latest_problem_title || "No submissions yet";
    const statusLabels = {
      "on-track": "On track",
      "needs-review": "Needs review",
      inactive: "No submissions",
    };
    const statusCell = document.createElement("td");
    statusCell.className = "py-3 px-4";
    statusCell.textContent =
      statusLabels[student.progress_status] || student.progress_status;
    const submittedCell = document.createElement("td");
    submittedCell.className = "py-3 px-4 text-slate-300";
    submittedCell.textContent = student.latest_submitted_at
      ? new Date(student.latest_submitted_at).toLocaleDateString()
      : "No submissions";
    row.append(
      Object.assign(document.createElement("td"), {
        className: "py-3 px-4",
        textContent: `Division ${student.division}`,
      }),
      solvedCell,
      latestCell,
      statusCell,
      submittedCell,
    );
    facultyProgressBody.append(row);
  });

  document.getElementById("faculty-progress-total").textContent =
    data.summary.active_student_count;
  document.getElementById("faculty-progress-average").textContent = Number(
    data.summary.average_solved,
  ).toFixed(1);
  document.getElementById("faculty-progress-reviews").textContent =
    data.summary.pending_review_count;
  document.getElementById("faculty-progress-pass-rate").textContent =
    `${Number(data.summary.pass_rate).toFixed(1)}%`;
  filterFacultyProgress();
}

async function loadFacultyStudentProgress() {
  const token = sessionStorage.getItem("authToken");
  facultyProgressBody.replaceChildren();
  try {
    if (!token)
      throw new Error(
        "Sign in with an approved faculty account to view student progress.",
      );
    const response = await fetch("/api/supervisor/student-progress", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    if (!response.ok)
      throw new Error(data.detail || "Unable to load student progress.");
    renderFacultyStudentProgress(data);
  } catch (error) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.className = "py-8 px-4 text-center text-rose-300";
    cell.colSpan = 6;
    cell.textContent = error.message || "Unable to load student progress.";
    row.append(cell);
    facultyProgressBody.append(row);
    document.getElementById("faculty-progress-count").textContent =
      "Progress unavailable";
    [
      "faculty-progress-total",
      "faculty-progress-average",
      "faculty-progress-reviews",
      "faculty-progress-pass-rate",
    ].forEach((id) => {
      document.getElementById(id).textContent = "—";
    });
  }
}

facultyProgressSearch.addEventListener("input", filterFacultyProgress);
facultyProgressDivision.addEventListener("change", filterFacultyProgress);
document
  .getElementById("faculty-progress-refresh")
  .addEventListener("click", loadFacultyStudentProgress);

function showUnavailableHistory(tableId, columnCount, message) {
  const tableBody = document.getElementById(tableId);
  const row = document.createElement("tr");
  const cell = document.createElement("td");
  cell.className = "py-8 px-4 text-center text-slate-400";
  cell.colSpan = columnCount;
  cell.textContent = message;
  row.append(cell);
  tableBody.replaceChildren(row);
}

showUnavailableHistory(
  "approved-table-body",
  8,
  "Approved-student history is not connected to live records.",
);
showUnavailableHistory(
  "rejected-table-body",
  7,
  "Rejected-student history is not connected to live records.",
);
document.getElementById("approved-footer-count").textContent =
  "No live approved-student history is connected.";
document.getElementById("rejected-footer-count").textContent =
  "No live rejected-student history is connected.";
["badge-nav-approved", "badge-nav-rejected", "badge-nav-activity"].forEach(
  (id) => {
    document.getElementById(id).classList.add("hidden");
  },
);

const activityList = document.getElementById("activity-items-list");

function renderActivityLog(entries) {
  activityList.replaceChildren();
  if (!entries.length) {
    const emptyState = document.createElement("p");
    emptyState.className = "py-8 text-center text-sm text-slate-400";
    emptyState.textContent = "No activity has been recorded yet.";
    activityList.append(emptyState);
    return;
  }
  entries.forEach((entry) => {
    const item = document.createElement("article");
    item.className =
      "activity-item bg-slate-900/60 border border-white/10 rounded-lg p-4";
    item.dataset.category = entry.category;
    const title = document.createElement("h3");
    title.className = "text-white font-medium";
    title.textContent = entry.description;
    const metadata = document.createElement("p");
    metadata.className = "text-xs text-slate-400 mt-1";
    metadata.textContent = `${entry.actor_name} • ${new Date(entry.created_at).toLocaleString()}`;
    item.append(title, metadata);
    activityList.append(item);
  });
}

async function loadActivityLog() {
  const token = sessionStorage.getItem("authToken");
  if (!token) return renderActivityLog([]);
  try {
    const response = await fetch("/api/faculty/activity", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const entries = await response.json();
    if (!response.ok) throw new Error(entries.detail || "Unable to load activity.");
    renderActivityLog(entries);
  } catch (error) {
    renderActivityLog([]);
    showToast(error.message || "Unable to load activity.", false, "error");
  }
}

loadActivityLog();

// Activity Log Filter Chips
const activityChips = document.querySelectorAll(".activity-chip");

activityChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    activityChips.forEach((c) => {
      c.classList.remove("bg-white/15", "text-white");
      c.classList.add("bg-white/5", "text-slate-300");
    });
    chip.classList.add("bg-white/15", "text-white");
    chip.classList.remove("bg-white/5", "text-slate-300");

    const category = chip.dataset.category;
    activityList.querySelectorAll(".activity-item").forEach((item) => {
      if (category === "all" || item.dataset.category === category) {
        item.classList.remove("hidden");
      } else {
        item.classList.add("hidden");
      }
    });
  });
});

// Pending Approvals State and Interactivity
let lastAction = null;
let verifiedCount = 0;
let rejectedCount = 0;

function updateMetricsAndCounters() {
  const visibleActiveRows = Array.from(
    document.querySelectorAll("#applications-table-body tr"),
  ).filter(
    (r) =>
      !r.classList.contains("hidden") &&
      !r.dataset.processed &&
      !r.dataset.empty,
  );
  const count = visibleActiveRows.length;
  const totalPending = Array.from(
    document.querySelectorAll("#applications-table-body tr"),
  ).filter((r) => !r.dataset.processed && !r.dataset.empty).length;
  const flaggedCount = Array.from(
    document.querySelectorAll("#applications-table-body tr"),
  ).filter((row) => row.dataset.flagged === "true").length;
  const priorityCount = Array.from(
    document.querySelectorAll("#applications-table-body tr"),
  ).filter((row) => row.dataset.priority === "true").length;

  document.getElementById("queue-count").innerText = totalPending;
  document.getElementById("badge-nav-pending").innerText = totalPending;
  document.getElementById("metric-pending").innerText =
    `${totalPending} Applications`;
  document.getElementById("total-count").innerText = totalPending;
  document.getElementById("visible-count").innerText =
    count > 0 ? `1-${count}` : "0";
  document.getElementById("queue-counter-badge").innerHTML =
    `Showing <span id="queue-count">${totalPending}</span> pending application${totalPending === 1 ? "" : "s"}`;
  document.getElementById("filter-all").innerText =
    `All Pending (${totalPending})`;
  document.getElementById("filter-flagged").innerText =
    `Flagged (${flaggedCount})`;
  document.getElementById("filter-priority").innerText =
    `High Priority (${priorityCount})`;
  updateSelection();
}

function showToast(message, allowUndo = false, icon = "info") {
  const toast = document.getElementById("toast-banner");
  const toastMsg = document.getElementById("toast-message");
  const toastIcon = document.getElementById("toast-icon");
  const undoBtn = document.getElementById("toast-undo");

  toastMsg.innerText = message;
  toastIcon.innerText = icon;
  toast.classList.remove("hidden");

  if (allowUndo) {
    undoBtn.classList.remove("hidden");
  } else {
    undoBtn.classList.add("hidden");
  }

  if (!allowUndo) {
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 4000);
  }
}

function makeCell(className, text) {
  const cell = document.createElement("td");
  cell.className = className;
  cell.textContent = text;
  return cell;
}

function renderPendingStudents(students) {
  const tableBody = document.getElementById("applications-table-body");
  tableBody.replaceChildren();

  if (!students.length) {
    const row = document.createElement("tr");
    row.dataset.empty = "true";
    const cell = makeCell(
      "py-8 px-4 text-center text-slate-300",
      "No pending student registrations.",
    );
    cell.colSpan = 7;
    row.append(cell);
    tableBody.append(row);
  }

  students.forEach((student) => {
    const row = document.createElement("tr");
    row.className = "hover:bg-slate-800/40 transition-colors group";
    row.id = `row-${student.id}`;
    row.dataset.id = student.id;
    row.dataset.branch = student.branch;
    row.dataset.division = student.division;
    row.dataset.flagged = "false";
    row.dataset.priority = "false";

    const checkboxCell = document.createElement("td");
    checkboxCell.className = "py-3.5 px-4 text-center";
    checkboxCell.innerHTML =
      '<input class="row-checkbox w-4 h-4 rounded border-white/20 text-white focus:ring-0 cursor-pointer" type="checkbox">';
    row.append(checkboxCell);

    const identityCell = document.createElement("td");
    identityCell.className = "py-3.5 px-4";
    const identity = document.createElement("div");
    identity.className = "flex items-center gap-3";
    const initials = student.name
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase();
    const avatar = document.createElement("div");
    avatar.className =
      "w-8 h-8 rounded-full bg-white/5 flex items-center justify-center font-code-inline text-code-inline font-medium text-white";
    avatar.textContent = initials;
    const details = document.createElement("div");
    details.className = "flex flex-col min-w-0";
    const name = document.createElement("span");
    name.className = "font-medium text-white truncate";
    name.textContent = student.name;
    const email = document.createElement("span");
    email.className = "text-slate-300 text-[12px] truncate";
    email.textContent = student.email;
    details.append(name, email);
    identity.append(avatar, details);
    identityCell.append(identity);
    row.append(identityCell);

    row.append(makeCell("py-3.5 px-4", student.division));
    row.append(makeCell("py-3.5 px-4", student.branch));
    row.append(
      makeCell(
        "py-3.5 px-4 font-code-inline text-code-inline",
        student.enrollment_number,
      ),
    );
    row.append(
      makeCell(
        "py-3.5 px-4 text-slate-300 whitespace-nowrap",
        "Pending review",
      ),
    );

    const actionCell = document.createElement("td");
    actionCell.className = "py-3.5 px-4 text-right pr-6 action-cell";
    const actions = document.createElement("div");
    actions.className = "flex items-center justify-end gap-2";
    const approveButton = document.createElement("button");
    approveButton.className =
      "rounded px-2.5 py-1 text-xs font-medium text-emerald-300 bg-emerald-500/15 border border-emerald-500/30 hover:bg-emerald-500/25 transition-colors";
    approveButton.textContent = "Approve";
    approveButton.addEventListener("click", () =>
      updateStudentApproval(student.id, student.name, true),
    );
    const rejectButton = document.createElement("button");
    rejectButton.className =
      "rounded px-2.5 py-1 text-xs font-medium text-rose-300 bg-rose-500/15 border border-rose-500/30 hover:bg-rose-500/25 transition-colors";
    rejectButton.textContent = "Reject";
    rejectButton.addEventListener("click", () =>
      updateStudentApproval(student.id, student.name, false),
    );
    actions.append(approveButton, rejectButton);
    actionCell.append(actions);
    row.append(actionCell);
    tableBody.append(row);
  });

  applyFilters();
}

async function loadPendingStudents() {
  document.getElementById("applications-table-body").replaceChildren();
  const token = sessionStorage.getItem("authToken");
  if (!token) {
    renderPendingStudents([]);
    showToast(
      "Sign in with an approved faculty account to review registrations.",
      false,
      "lock",
    );
    return;
  }

  try {
    const response = await fetch("/api/faculty/pending-students", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const students = await response.json();
    if (!response.ok)
      throw new Error(
        students.detail || "Unable to load pending registrations.",
      );
    renderPendingStudents(students);
  } catch (error) {
    showToast(
      error.message || "Unable to load pending registrations.",
      false,
      "error",
    );
  }
}

async function updateStudentApproval(
  id,
  studentName,
  approved,
  skipConfirmation = false,
) {
  if (
    !approved &&
    !skipConfirmation &&
    !confirm(
      `Are you sure you want to reject the application for ${studentName}?`,
    )
  )
    return;
  const token = sessionStorage.getItem("authToken");
  const row = document.getElementById(`row-${id}`);

  try {
    const response = await fetch(`/api/faculty/students/${id}/approve`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ approved }),
    });
    const result = await response.json();
    if (!response.ok)
      throw new Error(result.detail || "Unable to update this registration.");

    if (row) row.remove();
    if (approved) {
      verifiedCount += 1;
      document.getElementById("metric-verified").innerText =
        String(verifiedCount);
      document.getElementById("badge-nav-approved").innerText = verifiedCount;
    } else {
      rejectedCount += 1;
      document.getElementById("badge-nav-rejected").innerText = rejectedCount;
    }
    showToast(result.detail, false, approved ? "check_circle" : "block");
    updateMetricsAndCounters();
  } catch (error) {
    showToast(
      error.message || "Unable to update this registration.",
      false,
      "error",
    );
  }
}

window.approveApplication = (id, studentName) =>
  updateStudentApproval(id, studentName, true);
window.rejectApplication = (id, studentName, skipConfirmation = false) =>
  updateStudentApproval(id, studentName, false, skipConfirmation);

// Checkbox and Selection Logic
const selectAllCheckbox = document.getElementById("select-all");
const batchApproveBtn = document.getElementById("batch-approve");
const batchRejectBtn = document.getElementById("batch-reject");
const selectedCountText = document.getElementById("selected-count");

function updateSelection() {
  const visibleCheckboxes = Array.from(
    document.querySelectorAll(
      "#applications-table-body tr:not(.hidden) .row-checkbox",
    ),
  );
  const checked = visibleCheckboxes.filter((cb) => cb.checked);
  if (selectedCountText) selectedCountText.innerText = checked.length;

  if (checked.length > 0) {
    batchApproveBtn.disabled = false;
    batchRejectBtn.disabled = false;
    batchApproveBtn.classList.remove("opacity-50", "cursor-not-allowed");
    batchApproveBtn.classList.add(
      "bg-white/15",
      "text-white",
      "hover:bg-white/20",
      "hover:text-white",
    );
    batchRejectBtn.classList.remove("opacity-50", "cursor-not-allowed");
    batchRejectBtn.classList.add(
      "bg-white/15",
      "text-white",
      "hover:bg-white/20",
    );
  } else {
    batchApproveBtn.disabled = true;
    batchRejectBtn.disabled = true;
    batchApproveBtn.classList.add("opacity-50", "cursor-not-allowed");
    batchApproveBtn.classList.remove(
      "bg-white/15",
      "text-white",
      "hover:bg-white/20",
      "hover:text-white",
    );
    batchRejectBtn.classList.add("opacity-50", "cursor-not-allowed");
    batchRejectBtn.classList.remove(
      "bg-white/15",
      "text-white",
      "hover:bg-white/20",
    );
  }

  if (selectAllCheckbox) {
    selectAllCheckbox.checked =
      visibleCheckboxes.length > 0 &&
      checked.length === visibleCheckboxes.length;
  }
}

if (selectAllCheckbox) {
  selectAllCheckbox.addEventListener("change", (e) => {
    const visibleCheckboxes = document.querySelectorAll(
      "#applications-table-body tr:not(.hidden) .row-checkbox",
    );
    visibleCheckboxes.forEach((cb) => {
      cb.checked = e.target.checked;
    });
    updateSelection();
  });
}

document
  .getElementById("applications-table-body")
  .addEventListener("change", (e) => {
    if (e.target.classList.contains("row-checkbox")) {
      updateSelection();
    }
  });

batchApproveBtn.addEventListener("click", async () => {
  const checkedBoxes = Array.from(
    document.querySelectorAll(
      "#applications-table-body tr:not(.hidden) .row-checkbox:checked",
    ),
  );
  for (const cb of checkedBoxes) {
    const row = cb.closest("tr");
    const id = row.dataset.id;
    const name = row.querySelector(".font-medium").innerText;
    await window.approveApplication(id, name);
  }
});

batchRejectBtn.addEventListener("click", async () => {
  const checkedBoxes = Array.from(
    document.querySelectorAll(
      "#applications-table-body tr:not(.hidden) .row-checkbox:checked",
    ),
  );
  if (confirm(`Reject ${checkedBoxes.length} selected applications?`)) {
    for (const cb of checkedBoxes) {
      const row = cb.closest("tr");
      const id = row.dataset.id;
      const name = row.querySelector(".font-medium").innerText;
      await window.rejectApplication(id, name, true);
    }
  }
});

// Filter & Search Logic for Pending Approvals
const searchInput = document.getElementById("student-search");
const branchSelect = document.getElementById("branch-filter");
const divisionSelect = document.getElementById("division-filter");
const filterTabs = document.querySelectorAll(".filter-tab");
let activeTab = "all";

function applyFilters() {
  const term = searchInput.value.toLowerCase().trim();
  const branch = branchSelect.value;
  const division = divisionSelect.value;
  const rows = document.querySelectorAll("#applications-table-body tr");

  rows.forEach((row) => {
    const text = row.innerText.toLowerCase();
    const rowBranch = row.dataset.branch;
    const rowDivision = row.dataset.division;
    const isFlagged = row.dataset.flagged === "true";
    const isPriority = row.dataset.priority === "true";

    const matchesSearch = !term || text.includes(term);
    const matchesBranch = branch === "ALL" || rowBranch === branch;
    const matchesDivision = division === "ALL" || rowDivision === division;

    let matchesTab = true;
    if (activeTab === "flagged") matchesTab = isFlagged;
    if (activeTab === "priority") matchesTab = isPriority;

    if (matchesSearch && matchesBranch && matchesDivision && matchesTab) {
      row.classList.remove("hidden");
    } else {
      row.classList.add("hidden");
    }
  });

  updateMetricsAndCounters();
}

if (searchInput) searchInput.addEventListener("input", applyFilters);
if (branchSelect) branchSelect.addEventListener("change", applyFilters);
if (divisionSelect) divisionSelect.addEventListener("change", applyFilters);

filterTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    filterTabs.forEach((t) => {
      t.classList.remove(
        "bg-slate-900/60",
        "border",
        "border-white/10",
        "backdrop-blur-xl",
        "shadow-2xl",
        "text-white",
      );
      t.classList.add("text-slate-300");
    });
    tab.classList.add(
      "bg-slate-900/60",
      "border",
      "border-white/10",
      "backdrop-blur-xl",
      "shadow-2xl",
      "text-white",
    );
    tab.classList.remove("text-slate-300");
    activeTab = tab.dataset.filter;
    applyFilters();
  });
});

document.getElementById("bulk-review-btn").addEventListener("click", () => {
  const firstActive = document.querySelector(
    "#applications-table-body tr:not(.hidden) .action-cell button",
  );
  if (firstActive) {
    firstActive.scrollIntoView({ behavior: "smooth", block: "center" });
    firstActive.focus();
  }
});

loadPendingStudents();
loadFacultyStudentProgress();
