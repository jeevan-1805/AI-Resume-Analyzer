const modal =
    document.getElementById(
        "postModal"
    );

const openBtn =
    document.getElementById(
        "openPostModal"
    );

const closeBtn =
    document.getElementById(
        "closePostModal"
    );

openBtn.addEventListener(
    "click",
    () => {

        modal.style.display =
            "block";

    }
);

closeBtn.addEventListener(
    "click",
    () => {

        modal.style.display =
            "none";

    }
);
window.addEventListener(
    "click",
    (event) => {

        if(
            event.target === modal
        ){

            modal.style.display =
                "none";

        }

    }
);