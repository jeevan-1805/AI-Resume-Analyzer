// ===============================
// ATS SCORE
// ===============================

console.log("ATS:", atsScore);

console.log("Strength:", strengthScore);

console.log("Feedback:", aiFeedback);

console.log("Job Roles:", jobRoles);

console.log("Job Roles Type:", typeof jobRoles);

console.log("Is Array:", Array.isArray(jobRoles));

document.getElementById("atsScore").innerText =
    atsScore + "%";

const angle = (atsScore / 100) * 360;

document.getElementById("atsRing").style.background =
    `conic-gradient(#1976d2 ${angle}deg, #e0e0e0 ${angle}deg)`;


// ===============================
// STRENGTH SCORE
// ===============================

const strengthPercent = (strengthScore / 10) * 100;

document.getElementById("strengthFill").style.width =
    strengthPercent + "%";

document.getElementById("strengthScore").innerText =
    strengthScore + " / 10";


// ===============================
// AI FEEDBACK
// ===============================

const feedbackDiv =
    document.getElementById("feedbackText");

feedbackDiv.innerHTML = "";

if (aiFeedback) {

    const formattedFeedback =
        aiFeedback.replace(/\n/g, "<br>");

    feedbackDiv.innerHTML = formattedFeedback;
}


// ===============================
// JOB ROLE SECTION
// ===============================
let selectedJobRole = null;

const jobCardsContainer =
    document.getElementById("jobCards");

const optimizeJobBtn =
    document.getElementById("optimizeJobBtn");

const customJobRadio =
    document.getElementById("customJobRadio");

const customJobInput =
    document.getElementById("customJob");


jobCardsContainer.innerHTML = "";

optimizeJobBtn.disabled = true;


// ===============================
// CREATE JOB ROLE CARDS
// ===============================

if (Array.isArray(jobRoles) && jobRoles.length > 0) {

    jobRoles.forEach(role => {

        const card = document.createElement("button");

        card.type = "button";

        card.className = "job-card";

        card.setAttribute("aria-pressed", "false");

        card.textContent = role;


        card.addEventListener("click", () => {

            // disable custom input
            customJobRadio.checked = false;

            customJobInput.value = "";

            customJobInput.disabled = true;

            selectedJobRole = role;

            document.querySelectorAll(".job-card")
                .forEach(c => {
                    c.classList.remove("selected");
                });

            card.classList.add("selected");

            optimizeJobBtn.disabled = false;
        });

        jobCardsContainer.appendChild(card);
    });
}


// ===============================
// CUSTOM JOB ROLE
// ===============================


customJobRadio.addEventListener("change", () => {

    customJobInput.disabled = false;

    customJobInput.focus();

    document.querySelectorAll(".job-card")
        .forEach(c => {
            c.classList.remove("selected");
        });

    optimizeJobBtn.disabled =
        customJobInput.value.trim() === "";
});


customJobInput.addEventListener("input", () => {

    selectedJobRole =
        customJobInput.value.trim();

    optimizeJobBtn.disabled =
        selectedJobRole === "";
});

const saveTitleBtn =
    document.getElementById("saveTitleBtn");

const resumeTitleInput =
    document.getElementById("resumeTitleInput");


saveTitleBtn.addEventListener("click", async () => {

    const newTitle =
        resumeTitleInput.value.trim();

    if (!newTitle) {
        alert("Title cannot be empty");
        return;
    }

    try {

        const response = await fetch(
            `/resume/${resumeId}/update-title/`,
            {
                method: "POST",

                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type":
                        "application/x-www-form-urlencoded"
                },

                body:
                    `title=${encodeURIComponent(newTitle)}`
            }
        );

        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        alert("Title updated successfully");
        // Reloads the current page
        window.location.reload();

    } catch (error) {

        console.error(error);

        alert("Failed to update title");
    }
});

const executiveSummary =
    document.getElementById("ExecutiveSummary");
const optimizeGeneralBtn =
    document.getElementById("optimizeGeneralBtn");

    optimizeJobBtn.addEventListener("click", async () => {

    if (!selectedJobRole) {
        alert("Select a role first");
        return;
    }

    const response = await fetch(
        `/resume/${resumeId}/optimize-summary/`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },

            body: JSON.stringify({
                target_role: selectedJobRole
            })
        }
    );

    const data = await response.json();

    executiveSummary.value =
        data.optimized_summary;

    console.log(executiveSummary.value)
});

optimizeGeneralBtn.addEventListener("click", async () => {

    const response = await fetch(
        `/resume/${resumeId}/optimize-summary/`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken
            },

            body: JSON.stringify({
                general: true
            })
        }
    );

    const data = await response.json();

    executiveSummary.value =
        data.optimized_summary;

    console.log(executiveSummary.value)
});

document.getElementById("copyBtn")
    .addEventListener("click", () => {

    navigator.clipboard.writeText(
        executiveSummary.value
    );

    alert("Copied!");
});

const deleteBtn =
    document.getElementById("deleteResumeBtn");

deleteBtn.addEventListener("click", async () =>{
    const confirmed = confirm("Are you sure you want to delete this resume?");
    if (!confirmed){
        return;
    }

    const response = await fetch(
        `/resume/${resumeId}/delete/`,
        {
            method: "POST",
            headers: {
                "X-CSRFToken":csrfToken
            }
        }
    );
    const data = await response.json();

    if (data.success){
        alert("Resume deleted");
        window.location.href = "/";
    }
});