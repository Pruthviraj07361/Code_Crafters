(function initSupervisorDashboard() {
  const portalTitle = document.querySelector("header .font-headline-sm");
  const authUser = JSON.parse(sessionStorage.getItem("authUser") || "null");
  if (portalTitle && authUser?.role === "superuser") {
    portalTitle.textContent = "Admin Portal";
  }

  const isSuperuser = authUser?.role === "superuser";
  let loadAdminApprovals = null;
  if (isSuperuser) {
    const nav = document.getElementById("portal-nav");
    const approvalTab = document.createElement("a");
    approvalTab.className =
      "nav-tab flex items-center h-full px-space-2xs hover:text-white font-headline-sm text-label-md transition-colors border-b-2 cursor-pointer text-slate-300 border-transparent";
    approvalTab.dataset.view = "approvals";
    approvalTab.textContent = "Approvals";
    nav.append(approvalTab);

    const approvalView = document.createElement("div");
    approvalView.id = "view-approvals";
    approvalView.className = "view-panel flex flex-col w-full hidden";
    approvalView.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-space-lg pb-space-xl">
          <div>
            <h1 class="font-headline-lg text-headline-lg text-white font-semibold">Registration Approvals</h1>
            <p class="font-body-sm text-body-sm text-slate-400 mt-1">Review student and staff applications.</p>
          </div>
          <button class="h-9 px-space-md rounded border border-white/10 bg-white/5 text-white font-label-sm hover:bg-white/10" id="refresh-approvals" type="button">Refresh</button>
        </div>
        <p aria-live="polite" class="hidden mb-space-md text-sm text-rose-300" id="approval-error" role="status"></p>
        <section class="bg-slate-900/60 border border-white/10 rounded-lg overflow-hidden mb-space-xl">
          <div class="px-space-lg py-space-md border-b border-white/10"><h2 class="font-headline-sm text-white font-semibold">Student Applications</h2></div>
          <div class="divide-y divide-white/5" id="admin-pending-students"></div>
        </section>
        <section class="bg-slate-900/60 border border-white/10 rounded-lg overflow-hidden">
          <div class="px-space-lg py-space-md border-b border-white/10"><h2 class="font-headline-sm text-white font-semibold">Faculty and Staff Applications</h2></div>
          <div class="divide-y divide-white/5" id="admin-pending-staff"></div>
        </section>`;
    document.querySelector(".view-panel").parentElement.append(approvalView);

    const studentList = approvalView.querySelector("#admin-pending-students");
    const staffList = approvalView.querySelector("#admin-pending-staff");
    const approvalError = approvalView.querySelector("#approval-error");

    function showApprovalError(message) {
      approvalError.textContent = message;
      approvalError.classList.remove("hidden");
    }

    async function sendApproval(path, payload) {
      const response = await fetch(path, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("authToken")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok)
        throw new Error(result.detail || "Unable to update this application.");
      return result;
    }

    function makeApprovalButton(label, style, onClick) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `rounded px-3 py-1.5 text-sm font-medium ${style}`;
      button.textContent = label;
      button.addEventListener("click", onClick);
      return button;
    }

    async function reviewStudent(student, approved) {
      if (!approved && !confirm(`Reject the registration for ${student.name}?`))
        return;
      try {
        await sendApproval(`/api/faculty/students/${student.id}/approve`, {
          approved,
        });
        await loadAdminApprovals();
      } catch (error) {
        showApprovalError(error.message);
      }
    }

    function renderStudentApplications(students) {
      studentList.replaceChildren();
      if (!students.length) {
        studentList.textContent =
          "No student applications waiting for approval.";
        studentList.className =
          "px-space-lg py-space-md text-sm text-slate-400";
        return;
      }
      studentList.className = "divide-y divide-white/5";
      students.forEach((student) => {
        const row = document.createElement("div");
        row.className =
          "flex flex-col lg:flex-row lg:items-center justify-between gap-space-md px-space-lg py-space-md";
        const details = document.createElement("div");
        details.className = "flex flex-col text-sm text-white";
        details.append(
          makeStudentText("font-semibold", student.name),
          makeStudentText(
            "text-slate-400",
            `${student.email} · ${student.phone} · Division ${student.division} · ${student.enrollment_number}`,
          ),
        );
        const actions = document.createElement("div");
        actions.className = "flex items-center gap-space-xs";
        actions.append(
          makeApprovalButton(
            "Approve",
            "bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25",
            () => reviewStudent(student, true),
          ),
          makeApprovalButton(
            "Reject",
            "bg-rose-500/15 text-rose-200 hover:bg-rose-500/25",
            () => reviewStudent(student, false),
          ),
        );
        row.append(details, actions);
        studentList.append(row);
      });
    }

    async function reviewStaff(staff, approved, roleSelect) {
      if (!approved && !confirm(`Reject the application for ${staff.name}?`))
        return;
      try {
        await sendApproval(`/api/superuser/staff/${staff.id}/assign-role`, {
          approved,
          staff_type: roleSelect.value,
        });
        await loadAdminApprovals();
      } catch (error) {
        showApprovalError(error.message);
      }
    }

    function renderStaffApplications(staffMembers) {
      staffList.replaceChildren();
      if (!staffMembers.length) {
        staffList.textContent =
          "No faculty or staff applications waiting for approval.";
        staffList.className = "px-space-lg py-space-md text-sm text-slate-400";
        return;
      }
      staffList.className = "divide-y divide-white/5";
      staffMembers.forEach((staff) => {
        const row = document.createElement("div");
        row.className =
          "flex flex-col lg:flex-row lg:items-center justify-between gap-space-md px-space-lg py-space-md";
        const details = document.createElement("div");
        details.className = "flex flex-col text-sm text-white";
        details.append(
          makeStudentText("font-semibold", staff.name),
          makeStudentText(
            "text-slate-400",
            `${staff.email} · ${staff.phone} · Requested: ${staff.staff_type || "Admin review"}`,
          ),
        );
        const actions = document.createElement("div");
        actions.className = "flex flex-wrap items-center gap-space-xs";
        const roleSelect = document.createElement("select");
        roleSelect.className =
          "h-9 px-2 rounded border border-white/10 bg-slate-800 text-sm text-white";
        roleSelect.add(
          new Option(
            "Faculty",
            "faculty",
            false,
            staff.staff_type === "faculty",
          ),
        );
        roleSelect.add(
          new Option(
            "Supervisor",
            "supervisor",
            false,
            staff.staff_type === "supervisor",
          ),
        );
        if (!staff.staff_type) roleSelect.value = "faculty";
        actions.append(roleSelect);
        actions.append(
          makeApprovalButton(
            "Approve role",
            "bg-emerald-500/15 text-emerald-200 hover:bg-emerald-500/25",
            () => reviewStaff(staff, true, roleSelect),
          ),
          makeApprovalButton(
            "Reject",
            "bg-rose-500/15 text-rose-200 hover:bg-rose-500/25",
            () => reviewStaff(staff, false, roleSelect),
          ),
        );
        row.append(details, actions);
        staffList.append(row);
      });
    }

    loadAdminApprovals = async function () {
      approvalError.classList.add("hidden");
      try {
        const headers = {
          Authorization: `Bearer ${sessionStorage.getItem("authToken")}`,
        };
        const [studentResponse, staffResponse] = await Promise.all([
          fetch("/api/faculty/pending-students", { headers }),
          fetch("/api/superuser/pending-staff", { headers }),
        ]);
        const students = await studentResponse.json();
        const staffMembers = await staffResponse.json();
        if (!studentResponse.ok)
          throw new Error(
            students.detail || "Unable to load student applications.",
          );
        if (!staffResponse.ok)
          throw new Error(
            staffMembers.detail || "Unable to load staff applications.",
          );
        renderStudentApplications(students);
        renderStaffApplications(staffMembers);
      } catch (error) {
        showApprovalError(error.message || "Unable to load applications.");
      }
    };

    approvalView
      .querySelector("#refresh-approvals")
      .addEventListener("click", loadAdminApprovals);
    loadAdminApprovals();
  }

  // 1. Navigation Tab Switching
  const navTabs = document.querySelectorAll(".nav-tab");
  const viewPanels = document.querySelectorAll(".view-panel");

  function switchView(targetViewId) {
    navTabs.forEach((tab) => {
      const viewAttr = tab.getAttribute("data-view");
      if (viewAttr === targetViewId) {
        tab.classList.add("text-white", "border-white/40", "font-semibold");
        tab.classList.remove("text-slate-300", "border-transparent");
        tab.setAttribute("aria-current", "page");
      } else {
        tab.classList.remove("text-white", "border-white/40", "font-semibold");
        tab.classList.add("text-slate-300", "border-transparent");
        tab.removeAttribute("aria-current");
      }
    });

    viewPanels.forEach((panel) => {
      if (panel.id === "view-" + targetViewId) {
        panel.classList.remove("hidden");
      } else {
        panel.classList.add("hidden");
      }
    });
  }

  navTabs.forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault();
      const viewId = tab.getAttribute("data-view");
      switchView(viewId);
    });
  });
  if (isSuperuser) switchView("approvals");

  // 2. Manage Problem Statements View Logic
  const searchInput = document.getElementById("table-search");
  const divisionFilter = document.getElementById("division-filter");
  const statusTabs = document.querySelectorAll(".status-tab");
  let rows = Array.from(document.querySelectorAll(".problem-row"));
  const emptyState = document.getElementById("empty-state");
  const recordCounter = document.getElementById("record-counter");
  const footerCount = document.getElementById("footer-count");
  const selectAllCheck = document.getElementById("select-all-check");
  let rowCheckboxes = Array.from(document.querySelectorAll(".row-checkbox"));
  const selectedBadge = document.getElementById("selected-badge");
  const bulkAssignBtn = document.getElementById("bulk-assign-btn");
  const bulkArchiveBtn = document.getElementById("bulk-archive-btn");
  const clearFiltersBtn = document.getElementById("clear-filters-btn");

  let currentStatus = "all";

  function filterRows() {
    const query = (searchInput.value || "").trim().toLowerCase();
    const divVal = divisionFilter.value;
    let visibleCount = 0;

    rows.forEach((row) => {
      const id = row.getAttribute("data-id").toLowerCase();
      const status = row.getAttribute("data-status");
      const div = row.getAttribute("data-division");
      const textContent = row.textContent.toLowerCase();

      const matchesQuery =
        !query || id.includes(query) || textContent.includes(query);
      const matchesStatus = currentStatus === "all" || status === currentStatus;
      const matchesDiv = divVal === "all" || div.includes(divVal);

      if (matchesQuery && matchesStatus && matchesDiv) {
        row.style.display = "";
        visibleCount++;
      } else {
        row.style.display = "none";
      }
    });

    if (visibleCount === 0) {
      emptyState.classList.remove("hidden");
    } else {
      emptyState.classList.add("hidden");
    }

    recordCounter.textContent = `Showing ${visibleCount} statement${visibleCount === 1 ? "" : "s"}`;
    footerCount.textContent = `Showing ${visibleCount > 0 ? "1-" + visibleCount : "0"} of ${visibleCount} problem statements`;
    updateSelection();
  }

  if (searchInput) searchInput.addEventListener("input", filterRows);
  if (divisionFilter) divisionFilter.addEventListener("change", filterRows);

  statusTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      statusTabs.forEach((t) => {
        t.classList.remove(
          "bg-slate-900/60",
          "border",
          "border-white/10",
          "backdrop-blur-xl",
          "shadow-2xl",
          "text-white",
          "font-medium",
        );
        t.classList.add("text-slate-400");
      });
      tab.classList.add(
        "bg-slate-900/60",
        "border",
        "border-white/10",
        "backdrop-blur-xl",
        "shadow-2xl",
        "text-white",
        "font-medium",
      );
      tab.classList.remove("text-slate-400");
      currentStatus = tab.getAttribute("data-status");
      filterRows();
    });
  });

  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", () => {
      searchInput.value = "";
      divisionFilter.value = "all";
      currentStatus = "all";
      statusTabs.forEach((t) => {
        t.classList.remove(
          "bg-slate-900/60",
          "border",
          "border-white/10",
          "backdrop-blur-xl",
          "shadow-2xl",
          "text-white",
          "font-medium",
        );
        t.classList.add("text-slate-400");
      });
      statusTabs[0].classList.add(
        "bg-slate-900/60",
        "border",
        "border-white/10",
        "backdrop-blur-xl",
        "shadow-2xl",
        "text-white",
        "font-medium",
      );
      statusTabs[0].classList.remove("text-slate-400");
      filterRows();
    });
  }

  function updateSelection() {
    const visibleCheckboxes = rowCheckboxes.filter(
      (cb) => cb.closest(".problem-row").style.display !== "none",
    );
    const checkedBoxes = visibleCheckboxes.filter((cb) => cb.checked);
    if (selectedBadge) selectedBadge.textContent = checkedBoxes.length;

    if (bulkAssignBtn && bulkArchiveBtn) {
      if (checkedBoxes.length > 0) {
        bulkAssignBtn.removeAttribute("disabled");
        bulkArchiveBtn.removeAttribute("disabled");
      } else {
        bulkAssignBtn.setAttribute("disabled", "true");
        bulkArchiveBtn.setAttribute("disabled", "true");
      }
    }

    if (selectAllCheck) {
      if (
        visibleCheckboxes.length > 0 &&
        checkedBoxes.length === visibleCheckboxes.length
      ) {
        selectAllCheck.checked = true;
        selectAllCheck.indeterminate = false;
      } else if (checkedBoxes.length > 0) {
        selectAllCheck.checked = false;
        selectAllCheck.indeterminate = true;
      } else {
        selectAllCheck.checked = false;
        selectAllCheck.indeterminate = false;
      }
    }
  }

  if (selectAllCheck) {
    selectAllCheck.addEventListener("change", (e) => {
      const isChecked = e.target.checked;
      rowCheckboxes.forEach((cb) => {
        if (cb.closest(".problem-row").style.display !== "none") {
          cb.checked = isChecked;
        }
      });
      updateSelection();
    });
  }

  rowCheckboxes.forEach((cb) => {
    cb.addEventListener("change", updateSelection);
  });

  function makeProblemCell(className, text) {
    const cell = document.createElement("td");
    cell.className = className;
    cell.textContent = text;
    return cell;
  }

  function renderProblemStatements(problems) {
    const tableBody = document.getElementById("problems-tbody");
    tableBody.replaceChildren();

    problems.forEach((problem) => {
      const row = document.createElement("tr");
      const problemId = `PS-${String(problem.id).padStart(2, "0")}`;
      row.className = "problem-row hover:bg-slate-800/30 transition-colors";
      row.dataset.id = problemId;
      row.dataset.status = "published";
      row.dataset.division = "All Students";

      const checkboxCell = document.createElement("td");
      checkboxCell.className = "py-3 pl-space-md";
      checkboxCell.innerHTML =
        '<input class="row-checkbox rounded accent-white w-4 h-4 cursor-pointer" type="checkbox">';
      row.append(checkboxCell);

      const idCell = makeProblemCell("py-3 px-space-sm", problemId);
      idCell.classList.add(
        "font-code-inline",
        "text-code-inline",
        "font-semibold",
      );
      row.append(idCell);

      const titleCell = makeProblemCell(
        "py-3 px-space-sm font-medium",
        problem.title,
      );
      row.append(titleCell);
      row.append(
        makeProblemCell(
          "py-3 px-space-sm text-slate-400",
          new Date(problem.created_at).toLocaleDateString(),
        ),
      );
      row.append(
        makeProblemCell(
          "py-3 px-space-sm",
          problem.created_by_name || "Supervisor",
        ),
      );
      row.append(
        makeProblemCell(
          "py-3 pr-space-md text-right text-slate-400",
          "Available to students",
        ),
      );
      tableBody.append(row);
    });

    rows = Array.from(tableBody.querySelectorAll(".problem-row"));
    rowCheckboxes = Array.from(tableBody.querySelectorAll(".row-checkbox"));
    rowCheckboxes.forEach((checkbox) =>
      checkbox.addEventListener("change", updateSelection),
    );
    emptyState.textContent = problems.length
      ? "No problems match these filters."
      : "No problem statements yet.";
    filterRows();
  }

  async function loadProblemStatements() {
    document.getElementById("problems-tbody").replaceChildren();
    const token = sessionStorage.getItem("authToken");
    if (!token) {
      window.location.replace("/preview/");
      return;
    }

    try {
      const response = await fetch("/api/supervisor/problem-statements", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || "Unable to load problem statements.");
      renderProblemStatements(data);
    } catch (error) {
      window.alert(error.message || "Unable to load problem statements.");
    }
  }

  // Create Modal Interactions
  const openCreateBtn = document.getElementById("open-create-btn");
  const closeBtn = document.getElementById("close-modal-btn");
  const cancelBtn = document.getElementById("cancel-modal-btn");
  const saveBtn = document.getElementById("save-modal-btn");
  const modal = document.getElementById("create-modal");
  const problemFileInput = document.getElementById("problem-file");
  const problemTitleInput = document.getElementById("problem-title");
  const problemDescriptionInput = document.getElementById(
    "problem-description",
  );
  const problemTestCasesInput = document.getElementById("problem-test-cases");
  const problemFormMessage = document.getElementById("problem-form-message");

  problemFileInput.addEventListener("change", async () => {
    const file = problemFileInput.files[0];
    if (!file) return;

    if (!/\.(txt|md)$/i.test(file.name)) {
      problemFormMessage.textContent = "Choose a .txt or .md statement file.";
      problemFormMessage.classList.remove("hidden");
      problemFileInput.value = "";
      return;
    }

    try {
      const content = await file.text();
      if (!content.trim()) throw new Error("The selected file is empty.");
      problemDescriptionInput.value = content;
      if (!problemTitleInput.value.trim()) {
        problemTitleInput.value = file.name
          .replace(/\.(txt|md)$/i, "")
          .replace(/[_-]+/g, " ");
      }
      problemFormMessage.classList.add("hidden");
    } catch (error) {
      problemFormMessage.textContent =
        error.message || "Unable to read this file.";
      problemFormMessage.classList.remove("hidden");
      problemFileInput.value = "";
    }
  });

  function toggleModal(show) {
    if (show) {
      modal.classList.remove("hidden");
    } else {
      modal.classList.add("hidden");
    }
  }

  if (openCreateBtn)
    openCreateBtn.addEventListener("click", () => toggleModal(true));
  if (closeBtn) closeBtn.addEventListener("click", () => toggleModal(false));
  if (cancelBtn) cancelBtn.addEventListener("click", () => toggleModal(false));
  if (saveBtn)
    saveBtn.addEventListener("click", async () => {
      const message = document.getElementById("problem-form-message");
      const title = problemTitleInput.value.trim();
      const description = problemDescriptionInput.value.trim();
      const weekValue = document.getElementById("problem-week-number").value;
      const token = sessionStorage.getItem("authToken");
      message.classList.add("hidden");

      if (!title || !description) {
        message.textContent = "Enter a title and description.";
        message.classList.remove("hidden");
        return;
      }

      let testCases;
      try {
        testCases = JSON.parse(problemTestCasesInput.value);
      } catch (error) {
        message.textContent = "Enter grading test cases as valid JSON.";
        message.classList.remove("hidden");
        return;
      }

      saveBtn.disabled = true;
      try {
        const response = await fetch("/api/supervisor/problem-statements", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title,
            description,
            sample_input: document.getElementById("problem-sample-input").value,
            test_cases: testCases,
            week_number: weekValue ? Number(weekValue) : null,
          }),
        });
        const data = await response.json();
        if (!response.ok)
          throw new Error(data.detail || Object.values(data).flat().join(" "));

        problemTitleInput.value = "";
        problemDescriptionInput.value = "";
        problemFileInput.value = "";
        document.getElementById("problem-sample-input").value = "";
        problemTestCasesInput.value = "";
        document.getElementById("problem-week-number").value = "";
        toggleModal(false);
        await loadProblemStatements();
      } catch (error) {
        message.textContent =
          error.message || "Unable to save the problem statement.";
        message.classList.remove("hidden");
      } finally {
        saveBtn.disabled = false;
      }
    });

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) toggleModal(false);
    });
  }

  // 3. Student Progress View Filtering
  const studentSearch = document.getElementById("student-search");
  const studentCohortFilter = document.getElementById("student-cohort-filter");
  const studentBranchFilter = document.getElementById("student-branch-filter");
  const studentSemesterFilter = document.getElementById("student-semester-filter");
  const studentStatusTabs = document.querySelectorAll(".student-status-tab");
  const studentTableBody = document.getElementById("students-tbody");
  let studentRows = [];
  const studentRecordCounter = document.getElementById(
    "student-record-counter",
  );
  const studentFooterCount = document.getElementById("student-footer-count");
  let currentStudentStatus = "all";

  function appendStudentCell(row, className, content) {
    const cell = document.createElement("td");
    cell.className = className;
    if (content) cell.append(content);
    row.append(cell);
    return cell;
  }

  function makeStudentText(className, text, tagName = "span") {
    const element = document.createElement(tagName);
    element.className = className;
    element.textContent = text;
    return element;
  }

  function renderStudentProgress(students) {
    studentTableBody.replaceChildren();
    studentCohortFilter.replaceChildren(new Option("All Cohorts", "all"));
    const divisions = [
      ...new Set(students.map((student) => student.division)),
    ].sort();
    divisions.forEach((division) => {
      const option = new Option(`Division ${division}`, division);
      studentCohortFilter.append(option);
    });

    if (!students.length) {
      const row = document.createElement("tr");
      const cell = appendStudentCell(
        row,
        "py-6 px-space-md text-center text-slate-400",
        document.createTextNode("No approved student accounts found."),
      );
      cell.colSpan = 7;
      studentTableBody.append(row);
    } else {
      students.forEach((student) => {
        const row = document.createElement("tr");
        row.className = "student-row hover:bg-slate-800/30 transition-colors";
        row.dataset.cohort = student.division;
        row.dataset.status = student.progress_status;

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.className = "rounded accent-white w-4 h-4 cursor-pointer";
        const checkboxCell = appendStudentCell(row, "py-3 pl-space-md");
        checkboxCell.append(checkbox);

        const identity = document.createElement("div");
        identity.className = "flex flex-col";
        identity.append(
          makeStudentText(
            "font-body-md text-body-md text-white font-semibold",
            student.name,
          ),
          makeStudentText(
            "font-code-inline text-code-inline text-slate-400 font-mono text-xs",
            student.enrollment_number,
          ),
        );
        appendStudentCell(row, "py-3 px-space-sm", identity);

        const divisionBadge = makeStudentText(
          "inline-flex items-center gap-1 font-body-sm text-body-sm text-white bg-slate-800/40 border border-white/5 px-2 py-0.5 rounded-full font-medium",
          `Division ${student.division}`,
        );
        appendStudentCell(row, "py-3 px-space-sm", divisionBadge);

        const total = student.total_count;
        const solved = student.solved_count;
        const percentage = total ? Math.round((solved / total) * 100) : 0;
        const progress = document.createElement("span");
        progress.append(
          makeStudentText("font-semibold", `${solved} / ${total}`),
          document.createTextNode(" "),
          makeStudentText("text-slate-400 text-xs", `(${percentage}%)`),
        );
        appendStudentCell(
          row,
          "py-3 px-space-sm font-body-sm text-body-sm text-white font-medium",
          progress,
        );

        const latestProblem = document.createElement("div");
        latestProblem.className = "flex items-center gap-space-xs";
        if (student.latest_problem_id) {
          latestProblem.append(
            makeStudentText(
              "font-code-inline text-code-inline bg-white/5 px-1.5 py-0.5 rounded text-xs font-semibold",
              `PS-${String(student.latest_problem_id).padStart(2, "0")}`,
            ),
            makeStudentText(
              "font-body-sm text-body-sm text-white",
              student.latest_problem_title,
            ),
          );
        } else {
          latestProblem.append(
            makeStudentText(
              "font-body-sm text-slate-400",
              "No submissions yet",
            ),
          );
        }
        appendStudentCell(row, "py-3 px-space-sm", latestProblem);

        const labels = {
          passed: "Passed",
          failed: "Review Req.",
          pending: "Pending",
          checking: "Checking",
          submitted: "Submitted",
        };
        const status = document.createElement("div");
        status.className = "flex flex-col";
        const statusText = student.latest_status
          ? labels[student.latest_status] || student.latest_status
          : "No submissions";
        const statusTone =
          student.progress_status === "inactive"
            ? "text-slate-400"
            : "text-white";
        const statusLine = document.createElement("span");
        statusLine.className = `inline-flex items-center gap-1 font-label-sm text-label-sm ${statusTone} font-medium`;
        statusLine.append(
          makeStudentText(
            "w-1.5 h-1.5 rounded-full bg-slate-400 inline-block",
            "",
          ),
          document.createTextNode(statusText),
        );
        status.append(statusLine);
        const submittedDate = student.latest_submitted_at
          ? new Date(student.latest_submitted_at).toLocaleDateString()
          : "No submissions";
        status.append(
          makeStudentText("font-body-sm text-xs text-slate-400", submittedDate),
        );
        appendStudentCell(row, "py-3 px-space-sm", status);

        const reviewButton = makeStudentText(
          "px-2.5 py-1 rounded font-label-sm text-label-sm text-slate-400 hover:text-white hover:bg-white/10 transition-colors",
          student.latest_problem_id ? "Review Code" : "No submission",
          "button",
        );
        reviewButton.type = "button";
        appendStudentCell(row, "py-3 pr-space-md text-right", reviewButton);
        studentTableBody.append(row);
      });
    }

    studentRows = Array.from(studentTableBody.querySelectorAll(".student-row"));
    filterStudents();
  }

  async function loadStudentProgress() {
    studentTableBody.replaceChildren();
    const token = sessionStorage.getItem("authToken");
    if (!token) {
      studentTableBody.textContent =
        "Sign in as a supervisor or admin to view student records.";
      studentRows = [];
      filterStudents();
      return;
    }

    studentTableBody.textContent = "Loading student records...";
    try {
      const progressUrl = new URL(
        "/api/supervisor/student-progress",
        window.location.origin,
      );
      if (studentCohortFilter.value !== "all") {
        progressUrl.searchParams.set("division", studentCohortFilter.value);
      }
      if (studentBranchFilter?.value !== "all") {
        progressUrl.searchParams.set("branch", studentBranchFilter.value);
      }
      if (studentSemesterFilter?.value !== "all") {
        progressUrl.searchParams.set("semester", studentSemesterFilter.value);
      }
      const response = await fetch(progressUrl, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || "Unable to load student records.");
      renderStudentProgress(data.students);
      const branches = [...new Set(data.students.map((student) => student.branch))].sort();
      const semesters = [...new Set(data.students.map((student) => student.semester).filter(Boolean))].sort((a, b) => a - b);
      if (studentBranchFilter) {
        studentBranchFilter.replaceChildren(new Option("All Branches", "all"));
        branches.forEach((branch) => studentBranchFilter.add(new Option(branch, branch)));
      }
      if (studentSemesterFilter) {
        studentSemesterFilter.replaceChildren(new Option("All Semesters", "all"));
        semesters.forEach((semester) => studentSemesterFilter.add(new Option(`Semester ${semester}`, semester)));
      }
      document.getElementById("progress-total-students").textContent =
        data.summary.active_student_count;
      document.getElementById("progress-average-solved").textContent = Number(
        data.summary.average_solved,
      ).toFixed(1);
      document.getElementById("progress-pending-reviews").textContent =
        data.summary.pending_review_count;
      document.getElementById("progress-pass-rate").textContent =
        `${Number(data.summary.pass_rate).toFixed(1)}%`;
    } catch (error) {
      studentTableBody.textContent =
        error.message || "Unable to load student records.";
      studentRows = [];
      filterStudents();
    }
  }

  function filterStudents() {
    const query = (studentSearch.value || "").trim().toLowerCase();
    const cohortVal = studentCohortFilter.value;
    let count = 0;

    studentRows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      const cohort = row.getAttribute("data-cohort");
      const status = row.getAttribute("data-status");

      const matchesQuery = !query || text.includes(query);
      const matchesCohort = cohortVal === "all" || cohort === cohortVal;
      const matchesStatus =
        currentStudentStatus === "all" || status === currentStudentStatus;

      if (matchesQuery && matchesCohort && matchesStatus) {
        row.style.display = "";
        count++;
      } else {
        row.style.display = "none";
      }
    });

    if (studentRecordCounter) {
      studentRecordCounter.textContent = `Showing ${count} active student${count === 1 ? "" : "s"}`;
    }
    if (studentFooterCount) {
      studentFooterCount.textContent = `Showing ${count ? 1 : 0}-${count} of ${studentRows.length} enrolled students`;
    }
  }

  if (studentSearch) studentSearch.addEventListener("input", filterStudents);
  if (studentCohortFilter)
    studentCohortFilter.addEventListener("change", loadStudentProgress);
  if (studentBranchFilter)
    studentBranchFilter.addEventListener("change", loadStudentProgress);
  if (studentSemesterFilter)
    studentSemesterFilter.addEventListener("change", loadStudentProgress);
  loadStudentProgress();

  const publishAnnouncement = document.getElementById("publish-announcement");
  if (publishAnnouncement) {
    publishAnnouncement.addEventListener("click", async () => {
      const titleInput = document.getElementById("announcement-title");
      const messageInput = document.getElementById("announcement-message");
      const formMessage = document.getElementById("announcement-form-message");
      const title = titleInput.value.trim();
      const message = messageInput.value.trim();
      formMessage.classList.add("hidden");
      if (!title || !message) {
        formMessage.textContent = "Enter both a title and message.";
        formMessage.classList.remove("hidden");
        return;
      }
      publishAnnouncement.disabled = true;
      try {
        const response = await fetch("/api/supervisor/announcements", {
          method: "POST",
          headers: {
            Authorization: `******"authToken")}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ title, message }),
        });
        const data = await response.json();
        if (!response.ok)
          throw new Error(data.detail || "Unable to publish announcement.");
        titleInput.value = "";
        messageInput.value = "";
        formMessage.textContent = "Announcement published.";
        formMessage.classList.remove("hidden");
      } catch (error) {
        formMessage.textContent = error.message;
        formMessage.classList.remove("hidden");
      } finally {
        publishAnnouncement.disabled = false;
      }
    });
  }

  studentStatusTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      studentStatusTabs.forEach((t) => {
        t.classList.remove(
          "bg-slate-900/60",
          "border",
          "border-white/10",
          "backdrop-blur-xl",
          "shadow-2xl",
          "text-white",
          "font-medium",
        );
        t.classList.add("text-slate-400");
      });
      tab.classList.add(
        "bg-slate-900/60",
        "border",
        "border-white/10",
        "backdrop-blur-xl",
        "shadow-2xl",
        "text-white",
        "font-medium",
      );
      tab.classList.remove("text-slate-400");
      currentStudentStatus = tab.getAttribute("data-status");
      filterStudents();
    });
  });

  // 4. Meeting Schedule View Filtering
  const meetingSearch = document.getElementById("meeting-search");
  const meetingCohortFilter = document.getElementById("meeting-cohort-filter");
  const meetingStatusTabs = document.querySelectorAll(".meeting-status-tab");
  let meetingRows = Array.from(document.querySelectorAll(".meeting-row"));
  let currentMeetingStatus = "all";

  function filterMeetings() {
    const query = (meetingSearch.value || "").trim().toLowerCase();
    const cohortVal = meetingCohortFilter.value;

    meetingRows.forEach((row) => {
      const text = row.textContent.toLowerCase();
      const cohort = row.getAttribute("data-cohort");
      const mstatus = row.getAttribute("data-mstatus");

      const matchesQuery = !query || text.includes(query);
      const matchesCohort = cohortVal === "all" || cohort.includes(cohortVal);
      const matchesStatus =
        currentMeetingStatus === "all" || mstatus === currentMeetingStatus;

      if (matchesQuery && matchesCohort && matchesStatus) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  }

  if (meetingSearch) meetingSearch.addEventListener("input", filterMeetings);
  if (meetingCohortFilter)
    meetingCohortFilter.addEventListener("change", filterMeetings);

  meetingStatusTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      meetingStatusTabs.forEach((t) => {
        t.classList.remove(
          "bg-slate-900/60",
          "border",
          "border-white/10",
          "backdrop-blur-xl",
          "shadow-2xl",
          "text-white",
          "font-medium",
        );
        t.classList.add("text-slate-400");
      });
      tab.classList.add(
        "bg-slate-900/60",
        "border",
        "border-white/10",
        "backdrop-blur-xl",
        "shadow-2xl",
        "text-white",
        "font-medium",
      );
      tab.classList.remove("text-slate-400");
      currentMeetingStatus = tab.getAttribute("data-mstatus");
      filterMeetings();
    });
  });

  const scheduleSyncBtn = document.getElementById("schedule-sync-btn");
  const meetingModal = document.getElementById("meeting-modal");
  const meetingFormMessage = document.getElementById("meeting-form-message");
  let currentMeeting = null;

  function renderMeeting(meeting) {
    const tableBody = document.getElementById("meetings-tbody");
    tableBody.replaceChildren();
    currentMeeting = meeting;

    if (!meeting) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.className = "py-8 px-4 text-center text-slate-400";
      cell.colSpan = 7;
      cell.textContent = "No meeting has been scheduled yet.";
      row.append(cell);
      tableBody.append(row);
      meetingRows = [];
      document.getElementById("meeting-summary-count").textContent =
        "No meeting scheduled";
      document.getElementById("meeting-footer-count").textContent =
        "No meeting scheduled";
      return;
    }

    const row = document.createElement("tr");
    const scheduledFor = new Date(meeting.scheduled_for);
    const isUpcoming = scheduledFor >= new Date();
    row.className = "meeting-row hover:bg-slate-800/30 transition-colors";
    row.dataset.cohort = "All Cohorts";
    row.dataset.mstatus = isUpcoming ? "upcoming" : "confirmed";

    const titleCell = document.createElement("td");
    titleCell.className = "py-3 pl-space-md px-space-sm";
    const details = document.createElement("div");
    details.className = "flex flex-col";
    const title = document.createElement("span");
    title.className = "font-body-md text-white font-semibold";
    title.textContent = meeting.title;
    const notes = document.createElement("span");
    notes.className = "font-body-sm text-slate-400 text-xs";
    notes.textContent = meeting.notes || "No notes provided";
    details.append(title, notes);
    titleCell.append(details);
    row.append(titleCell);

    const addCell = (className, value) => {
      const cell = document.createElement("td");
      cell.className = className;
      cell.textContent = value;
      row.append(cell);
    };
    addCell("py-3 px-space-sm", "All Cohorts");
    addCell("py-3 px-space-sm", scheduledFor.toLocaleString());
    addCell("py-3 px-space-sm", meeting.notes || "No location details");
    addCell("py-3 px-space-sm", meeting.updated_by_name || "Supervisor");
    addCell("py-3 px-space-sm", isUpcoming ? "Upcoming" : "Confirmed");

    const actionCell = document.createElement("td");
    actionCell.className = "py-3 pr-space-md text-right";
    const editButton = document.createElement("button");
    editButton.className =
      "px-2 py-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-colors";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", openMeetingModal);
    actionCell.append(editButton);
    row.append(actionCell);
    tableBody.append(row);
    meetingRows = [row];
    filterMeetings();
    document.getElementById("meeting-summary-count").textContent =
      "Showing 1 scheduled meeting";
    document.getElementById("meeting-footer-count").textContent =
      "Showing 1 scheduled meeting";
  }

  async function loadMeeting() {
    document.getElementById("meetings-tbody").replaceChildren();
    meetingRows = [];
    const token = sessionStorage.getItem("authToken");
    if (!token) return;

    try {
      const response = await fetch("/api/supervisor/meeting", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      if (response.status === 404) {
        renderMeeting(null);
        return;
      }
      if (!response.ok)
        throw new Error(data.detail || "Unable to load the meeting schedule.");
      renderMeeting(data);
    } catch (error) {
      alert(error.message || "Unable to load the meeting schedule.");
    }
  }

  function openMeetingModal() {
    meetingFormMessage.classList.add("hidden");
    if (currentMeeting) {
      document.getElementById("meeting-title").value = currentMeeting.title;
      document.getElementById("meeting-slot").value = currentMeeting.slot || 1;
      document.getElementById("meeting-notes").value =
        currentMeeting.notes || "";
      const date = new Date(currentMeeting.scheduled_for);
      date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
      document.getElementById("meeting-scheduled-for").value = date
        .toISOString()
        .slice(0, 16);
    } else {
      document.getElementById("meeting-title").value = "";
      document.getElementById("meeting-slot").value = 1;
      document.getElementById("meeting-notes").value = "";
      document.getElementById("meeting-scheduled-for").value = "";
    }
    meetingModal.classList.remove("hidden");
  }

  async function saveMeeting() {
    const scheduledFor = new Date(
      document.getElementById("meeting-scheduled-for").value,
    );
    if (!Number.isFinite(scheduledFor.getTime())) {
      meetingFormMessage.textContent = "Choose a valid date and time.";
      meetingFormMessage.classList.remove("hidden");
      return;
    }

    const saveButton = document.getElementById("save-meeting-btn");
    saveButton.disabled = true;
    meetingFormMessage.classList.add("hidden");
    try {
      const response = await fetch("/api/supervisor/meeting", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${sessionStorage.getItem("authToken")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: document.getElementById("meeting-title").value.trim(),
          slot: Number(document.getElementById("meeting-slot").value),
          notes: document.getElementById("meeting-notes").value,
          scheduled_for: scheduledFor.toISOString(),
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || Object.values(data).flat().join(" "));
      meetingModal.classList.add("hidden");
      renderMeeting(data);
    } catch (error) {
      meetingFormMessage.textContent =
        error.message || "Unable to save the meeting.";
      meetingFormMessage.classList.remove("hidden");
    } finally {
      saveButton.disabled = false;
    }
  }

  scheduleSyncBtn.addEventListener("click", openMeetingModal);
  document
    .getElementById("save-meeting-btn")
    .addEventListener("click", saveMeeting);
  document
    .getElementById("close-meeting-modal")
    .addEventListener("click", () => meetingModal.classList.add("hidden"));
  document
    .getElementById("cancel-meeting-modal")
    .addEventListener("click", () => meetingModal.classList.add("hidden"));

  loadProblemStatements();
  loadMeeting();
})();
