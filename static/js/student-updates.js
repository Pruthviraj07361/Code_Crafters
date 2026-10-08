(function () {
  const feed = document.getElementById("student-meeting-feed");
  const token = sessionStorage.getItem("authToken");
  if (!feed || !token) return;

  fetch("/api/student/updates", {
    headers: { Authorization: "Bearer " + token },
  })
    .then(async (response) => {
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to load updates.");
      return data;
    })
    .then((data) => {
      const meetings = data.meetings || [];
      const announcements = data.announcements || [];
      if (!meetings.length && !announcements.length) {
        feed.textContent = "No meetings or announcements yet.";
        return;
      }

      const cards = [];
      announcements.forEach((announcement) => {
        const card = document.createElement("article");
        card.className =
          "bg-slate-900/60 border border-white/10 backdrop-blur-xl shadow-2xl rounded-lg p-space-md flex flex-col space-y-space-xs";
        const title = document.createElement("h3");
        title.className = "font-headline-sm text-headline-sm text-white";
        title.textContent = announcement.title;
        const message = document.createElement("p");
        message.className = "font-body-sm text-body-sm text-slate-300";
        message.textContent = announcement.message;
        card.append(title, message);
        cards.push(card);
      });

      meetings.forEach((meeting) => {
        const card = document.createElement("article");
        card.className =
          "bg-slate-900/60 border border-white/10 backdrop-blur-xl shadow-2xl rounded-lg p-space-md flex flex-col space-y-space-xs";
        const title = document.createElement("h3");
        title.className = "font-headline-sm text-headline-sm text-white";
        title.textContent = meeting.title;
        const scheduled = document.createElement("p");
        scheduled.className = "font-body-sm text-body-sm text-slate-300";
        scheduled.textContent = new Date(meeting.scheduled_for).toLocaleString();
        card.append(title, scheduled);
        if (meeting.notes) {
          const notes = document.createElement("p");
          notes.className =
            "font-body-sm text-body-sm text-slate-300 pt-1 border-t border-white/10";
          notes.textContent = meeting.notes;
          card.append(notes);
        }
        cards.push(card);
      });
      feed.replaceChildren(...cards);
      const nextMeeting = document.getElementById("metric-next-meeting");
      if (nextMeeting && meetings.length) {
        nextMeeting.textContent = `Next: ${new Date(meetings[0].scheduled_for).toLocaleString()}`;
      }
    })
    .catch((error) => {
      feed.textContent = error.message || "Unable to load updates.";
    });
})();
