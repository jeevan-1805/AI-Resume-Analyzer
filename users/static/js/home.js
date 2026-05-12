const analyzeBtn = document.getElementById("analyzeBtn");
const uploadBox = document.getElementById("uploadBox");
const resumeInput = document.getElementById("resumeFile");
const uploadText = document.getElementById("uploadText");

uploadBox.addEventListener("click", () => {
    resumeInput.click();
});

resumeInput.addEventListener("change", () => {
    if (resumeInput.files.length > 0) {
        uploadText.textContent = resumeInput.files[0].name;
    }
});

uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.classList.add("dragover");
});

uploadBox.addEventListener("dragleave", () => {
    uploadBox.classList.remove("dragover");
});

uploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadBox.classList.remove("dragover");

    const file = e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
        resumeInput.files = e.dataTransfer.files;
        uploadText.textContent = file.name;
    } else {
        alert("Only PDF files are allowed.");
    }
});

analyzeBtn.addEventListener("click", async () => {
    const file = resumeInput.files[0];

    if (!file) {
        alert("Please upload a PDF resume.");
        return;
    }

    if (file.type !== "application/pdf") {
        alert("Only PDF files are allowed.");
        return;
    }

    document
            .getElementById("loadingOverlay")
            .classList.remove("hidden");

    
    const formData = new FormData();
    formData.append("resume", file);

    if (!isAuthenticated) {

        const reader = new FileReader();

        reader.onload = function () {

            sessionStorage.setItem(
                "pendingResume",
                reader.result
            );

            sessionStorage.setItem(
                "pendingResumeName",
                file.name
            );

            alert(
                "Do not close Tab. Your resume is on hold. Login or register to continue."
            );

            window.location.href = "/accounts/login/";
        };

        reader.readAsDataURL(file);

        return;
    }
    

    try {
        const response = await fetch("/analyze/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCookie("csrftoken")
            },
            body: formData
        });

        

        if (!response.ok) {
            document
                .getElementById("loadingOverlay")
                .classList.add("hidden");
            alert("Server error. Please try again.");
            return;
        }

        const data = await response.json();
        window.extractedResumeText = data.extracted_text;

        if (data.error) {
            alert(data.error);
            return;
        }

        window.location.href = `/resume/${data.resume_id}/`;

        
    } catch (error) {
        document
            .getElementById("loadingOverlay")
            .classList.add("hidden");
        console.error("Fatal JS error:", error);
        alert("Unexpected error. Check console for details.");
    }
});

window.addEventListener("load", async () => {
    console.log("AUTO UPLOAD CHECK STARTED");
    console.log(
        sessionStorage.getItem("pendingResume")
    );
    console.log(isAuthenticated);

    if (!isAuthenticated) {
        return;
    }

    const pendingResume =
        sessionStorage.getItem("pendingResume");

    const pendingResumeName =
        sessionStorage.getItem("pendingResumeName");

    if (!pendingResume || !pendingResumeName) {
        return;
    }

    // Convert Base64 back into Blob
    const response = await fetch(pendingResume);

    const blob = await response.blob();

    // Rebuild File object
    const file = new File(
        [blob],
        pendingResumeName,
        {
            type: "application/pdf"
        }
    );

    document
        .getElementById("loadingOverlay")
        .classList.remove("hidden");

    // Create form data
    const formData = new FormData();

    formData.append("resume", file);

    console.log("Uploading pending resume...");

    // Upload automatically
    const uploadResponse = await fetch("/analyze/", {
        method: "POST",

        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },

        body: formData
    });

    const data = await uploadResponse.json();

    console.log(data);
    

    // Clear temporary storage
    sessionStorage.removeItem("pendingResume");

    sessionStorage.removeItem("pendingResumeName");

    // Redirect to resume detail
    if (data.resume_id) {

        window.location.href =
            `/resume/${data.resume_id}/`;
    }
});