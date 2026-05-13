const sidebar =
    document.getElementById("sidebar");

const sidebarToggle =
    document.getElementById("sidebarToggle");

const sidebarOverlay =
    document.getElementById("sidebarOverlay");


if (sidebar && sidebarToggle && sidebarOverlay) {

    sidebarToggle.addEventListener("click", () => {

        sidebar.classList.toggle("active");

        sidebarOverlay.classList.toggle("active");
    });

    sidebarOverlay.addEventListener("click", () => {

        sidebar.classList.remove("active");

        sidebarOverlay.classList.remove("active");
    });
}