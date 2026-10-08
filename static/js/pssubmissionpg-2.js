(function () {
  const editor = document.getElementById("codeEditor");
  const gutter = document.getElementById("lineGutter");
  const cursorPos = document.getElementById("cursorPos");
  const runBtn = document.getElementById("runTestsBtn");
  const submitBtn = document.getElementById("submitCodeBtn");
  const drawer = document.getElementById("outputDrawer");
  const statusMsg = document.getElementById("statusMessage");
  const resetBtn = document.getElementById("resetCodeBtn");

  // Language dropdown elements
  const langSelectBtn = document.getElementById("langSelectBtn");
  const langMenu = document.getElementById("langMenu");
  const currentLangLabel = document.getElementById("currentLangLabel");
  const tabFileName = document.getElementById("tabFileName");
  const langButtons = langMenu
    ? langMenu.querySelectorAll("button[data-lang]")
    : [];
  const problemId = new URLSearchParams(window.location.search).get("problem");
  let selectedLanguage = "c";
  const backLink = document.querySelector('header [data-path="dashboard"]');
  if (backLink) backLink.href = "/preview/student/";

  const defaultCode = `#include <stdio.h>
  \nint main(void) {
    return 0;
  }`;

  // Toggle dropdown
  if (langSelectBtn && langMenu) {
    langSelectBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      langMenu.classList.toggle("hidden");
    });
    document.addEventListener("click", function (e) {
      if (!langMenu.contains(e.target) && !langSelectBtn.contains(e.target)) {
        langMenu.classList.add("hidden");
      }
    });
  }

  // Language switcher
  langButtons.forEach((btn) => {
    if (btn.dataset.lang !== "c") btn.classList.add("hidden");
    btn.addEventListener("click", function () {
      const file = this.getAttribute("data-file");
      const display = this.getAttribute("data-display");
      const lang = this.getAttribute("data-lang");
      selectedLanguage = lang;
      if (currentLangLabel) currentLangLabel.textContent = display;
      if (tabFileName) tabFileName.textContent = file;

      // update active checkmarks
      langButtons.forEach((b) => {
        const check = b.querySelector("[data-check]");
        if (check) {
          if (b === btn) {
            check.classList.remove("hidden");
          } else {
            check.classList.add("hidden");
          }
        }
      });
      if (langMenu) langMenu.classList.add("hidden");
    });
  });

  // Update lines in gutter
  function updateGutter() {
    if (!editor || !gutter) return;
    const lineCount = editor.value.split("\n").length;
    let numbers = "";
    for (let i = 1; i <= Math.max(lineCount, 22); i++) {
      numbers += i + "<br>";
    }
    gutter.innerHTML = numbers;
  }

  // Update Cursor Location Tracking
  function updateCursorInfo() {
    if (!editor || !cursorPos) return;
    const text = editor.value.substr(0, editor.selectionStart);
    const lines = text.split("\n");
    const line = lines.length;
    const col = lines[lines.length - 1].length + 1;
    cursorPos.textContent = `Ln ${line}, Col ${col}`;
  }

  // Support Tab indent insertion in textarea
  if (editor) {
    editor.addEventListener("keydown", function (e) {
      if (e.key === "Tab") {
        e.preventDefault();
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value =
          this.value.substring(0, start) + "    " + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 4;
        updateGutter();
        updateCursorInfo();
      }
    });

    editor.addEventListener("input", function () {
      updateGutter();
      updateCursorInfo();
    });

    editor.addEventListener("keyup", updateCursorInfo);
    editor.addEventListener("click", updateCursorInfo);
  }

  // Reset code behavior
  if (resetBtn && editor) {
    resetBtn.addEventListener("click", function () {
      editor.value = defaultCode;
      updateGutter();
      updateCursorInfo();
    });
  }

  async function loadProblem() {
    if (!problemId || !/^\d+$/.test(problemId)) {
      window.location.replace("/preview/student/");
      return;
    }

    const token = sessionStorage.getItem("authToken");
    if (!token) {
      document.getElementById("problemTitle").textContent =
        "Sign in to view this problem";
      document.getElementById("problemDescription").textContent =
        "Problem statements are loaded from the database for approved students.";
      return;
    }

    try {
      const response = await fetch(
        `/api/student/problem-statements/${problemId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      const problem = await response.json();
      if (!response.ok)
        throw new Error(
          problem.detail || "Unable to load this problem statement.",
        );

      document.getElementById("problemTitle").textContent =
        `PS-${String(problem.id).padStart(2, "0")}: ${problem.title}`;
      document.getElementById("problemDescription").textContent =
        problem.description;
      const sampleSection = document.getElementById("problemSampleSection");
      const sampleInput = document.getElementById("problemSampleInput");
      sampleSection.classList.toggle("hidden");
      sampleInput.textContent = problem.sample_input || "";
      const pageTitle = document.querySelector("header .font-headline-sm");
      if (pageTitle) pageTitle.textContent = problem.title;
      if (editor) {
        editor.value = defaultCode;
        updateGutter();
      }
    } catch (error) {
      document.getElementById("problemTitle").textContent =
        "Problem unavailable";
      document.getElementById("problemDescription").textContent =
        error.message || "Unable to load this problem statement.";
      submitBtn.disabled = true;
    }
  }

  // Run tests interaction
  if (runBtn && drawer) {
    runBtn.addEventListener("click", function () {
      drawer.classList.remove("hidden");
      statusMsg.textContent = "Automated code execution is not configured yet.";
      document.getElementById("statusIcon").textContent = "info";
      document.getElementById("outputDetails").textContent =
        "Use Submit Code to save your solution for review.";
    });
  }

  // Submission interaction
  if (submitBtn && drawer) {
    submitBtn.addEventListener("click", async function () {
      if (!editor || !editor.value.trim()) {
        drawer.classList.remove("hidden");
        statusMsg.textContent = "Write your solution before submitting.";
        document.getElementById("statusIcon").textContent = "error";
        document.getElementById("outputDetails").textContent = "";
        return;
      }

      const token = sessionStorage.getItem("authToken");
      if (!token) {
        drawer.classList.remove("hidden");
        statusMsg.textContent = "Sign in before submitting this solution.";
        document.getElementById("statusIcon").textContent = "info";
        document.getElementById("outputDetails").textContent =
          "Preview mode cannot submit or grade code. Log in, then reopen this problem.";
        return;
      }

      drawer.classList.remove("hidden");
      statusMsg.textContent = "Saving submission...";
      document.getElementById("statusIcon").textContent = "progress_activity";
      document.getElementById("outputDetails").textContent = "";
      submitBtn.disabled = true;
      try {
        const response = await fetch(
          `/api/student/problem-statements/${problemId}/submit`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              language: selectedLanguage,
              code: editor.value,
            }),
          },
        );
        const result = await response.json();
        if (!response.ok)
          throw new Error(
            result.detail || Object.values(result).flat().join(" "),
          );
        if (result.status === "pending") {
          statusMsg.textContent = "Submission queued for grading.";
          document.getElementById("statusIcon").textContent = "schedule";
          document.getElementById("outputDetails").textContent =
            "Your submission was saved. Refresh your submissions later to see the grading result.";
        } else if (result.status === "passed") {
          statusMsg.textContent = "Correct. All test cases passed.";
          document.getElementById("statusIcon").textContent = "check_circle";
        } else {
          statusMsg.textContent =
            "Incorrect. Review the test results and try again.";
          document.getElementById("statusIcon").textContent = "error";
        }
        document.getElementById("outputDetails").textContent =
          result.judge0_output || "";
      } catch (error) {
        statusMsg.textContent = error.message || "Unable to submit your code.";
        document.getElementById("statusIcon").textContent = "error";
        document.getElementById("outputDetails").textContent = "";
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  // Initial render
  updateGutter();
  loadProblem();
})();
