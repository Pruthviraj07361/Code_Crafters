(function () {
  const filterBtns = document.querySelectorAll(".filter-btn");
  const cardsContainer = document.getElementById("cards-container");
  let activeFilter = "all";

  function applyFilter() {
    cardsContainer.querySelectorAll(".problem-card").forEach((card) => {
      card.style.display =
        activeFilter === "all" || card.dataset.status === activeFilter
          ? "block"
          : "none";
    });
  }

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      activeFilter = btn.getAttribute("data-filter");

      // Style tabs
      filterBtns.forEach((b) => {
        b.classList.remove(
          "bg-slate-900/60",
          "border",
          "border-white/10",
          "backdrop-blur-xl",
          "shadow-2xl",
          "text-white",
          "font-medium",
        );
        b.classList.add("text-slate-400");
      });
      btn.classList.add(
        "bg-slate-900/60",
        "border",
        "border-white/10",
        "backdrop-blur-xl",
        "shadow-2xl",
        "text-white",
        "font-medium",
      );
      btn.classList.remove("text-slate-400");

      applyFilter();
    });
  });

  async function loadProblems() {
    const token = sessionStorage.getItem("authToken");
    cardsContainer.replaceChildren();
    if (!token) {
      cardsContainer.textContent = "Sign in to load problem statements.";
      return;
    }

    cardsContainer.textContent = "Loading problem statements...";
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [problemsResponse, submissionsResponse] = await Promise.all([
        fetch("/api/student/problem-statements", { headers }),
        fetch("/api/student/submissions", { headers }),
      ]);
      const problems = await problemsResponse.json();
      const submissions = await submissionsResponse.json();
      if (!problemsResponse.ok)
        throw new Error(
          problems.detail || "Unable to load problem statements.",
        );
      if (!submissionsResponse.ok)
        throw new Error(submissions.detail || "Unable to load submissions.");

      const assignedMetric = document.getElementById("metric-assigned");
      const pendingMetric = document.getElementById("metric-pending");
      const completedMetric = document.getElementById("metric-completed");
      if (assignedMetric)
        assignedMetric.textContent = `${problems.length} Assigned`;
      if (pendingMetric) {
        const pendingCount = problems.filter((problem) => {
          const submission = submissions.find(
            (item) => item.problem_statement === problem.id,
          );
          return !submission || submission.status !== "passed";
        }).length;
        pendingMetric.textContent = `${pendingCount} Pending`;
      }
      if (completedMetric) {
        const completedCount = problems.filter((problem) =>
          submissions.some(
            (item) =>
              item.problem_statement === problem.id && item.status === "passed",
          ),
        ).length;
        completedMetric.textContent = `${completedCount} Completed`;
      }

      cardsContainer.replaceChildren();
      if (!problems.length) {
        cardsContainer.textContent = "No problem statements are available yet.";
        return;
      }

      problems.forEach((problem) => {
        const latestSubmission = submissions.find(
          (submission) => submission.problem_statement === problem.id,
        );
        const isDone = latestSubmission && latestSubmission.status === "passed";
        const card = document.createElement("article");
        card.className =
          "problem-card group bg-slate-900/60 border border-white/10 backdrop-blur-xl shadow-2xl rounded-lg p-space-lg hover:border-white/30 transition-colors";
        card.dataset.status = isDone ? "done" : "pending";

        const header = document.createElement("div");
        header.className =
          "flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-xs";
        const identity = document.createElement("div");
        identity.className = "flex items-center gap-space-xs";
        const problemCode = document.createElement("span");
        problemCode.className =
          "font-code-inline text-code-inline px-2 py-0.5 rounded bg-white/5 text-white border border-white/10";
        problemCode.textContent = `PS-${String(problem.id).padStart(2, "0")}`;
        const title = document.createElement("h3");
        title.className =
          "font-headline-sm text-headline-sm text-white group-hover:text-slate-300";
        const titleLink = document.createElement("a");
        titleLink.href = `/preview/submission/?problem=${problem.id}`;
        titleLink.className =
          "hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2";
        titleLink.textContent = problem.title;
        title.append(titleLink);
        identity.append(problemCode, title);

        const status = document.createElement("span");
        status.className =
          "inline-flex items-center gap-1 font-label-sm text-label-sm px-2 py-0.5 rounded bg-white/5 text-white border border-white/10 self-start sm:self-auto";
        if (isDone) {
          const passedIcon = document.createElement("span");
          passedIcon.className = "material-symbols-outlined text-[14px]";
          passedIcon.textContent = "check";
          status.append(passedIcon, document.createTextNode("Passed"));
        } else {
          status.textContent =
            latestSubmission?.status === "failed"
              ? "Failed"
              : latestSubmission?.status === "checking"
                ? "Checking"
                : "Pending";
        }
        header.append(identity, status);

        const description = document.createElement("p");
        description.className =
          "font-body-md text-body-md text-slate-300 mt-space-xs leading-relaxed";
        description.textContent = problem.week_number
          ? `Week ${problem.week_number} problem statement`
          : "Open the problem statement to write and submit your code.";

        const footer = document.createElement("div");
        footer.className =
          "mt-space-md pt-space-xs border-t border-white/10 flex items-center justify-between gap-space-xs text-slate-400 font-label-sm text-label-sm";
        const week = document.createElement("span");
        week.textContent = problem.week_number
          ? `Week ${problem.week_number}`
          : "Coding assignment";
        const link = document.createElement("a");
        link.className =
          "inline-flex items-center gap-1 font-label-md text-label-md text-white font-medium hover:underline";
        link.href = `/preview/submission/?problem=${problem.id}`;
        link.textContent = isDone ? "View Submission" : "View Statement";
        footer.append(week, link);
        card.append(header, description, footer);
        cardsContainer.append(card);
      });
      applyFilter();
    } catch (error) {
      cardsContainer.textContent =
        error.message || "Unable to load problem statements.";
    }
  }

  loadProblems();
})();
