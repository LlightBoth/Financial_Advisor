document.addEventListener("DOMContentLoaded", function() {
    const formCard = document.getElementById("advisor-form-card");
    const adviceCard = document.getElementById("advice-card");
    const form = document.getElementById("advisor-form");
    const closeBtn = document.getElementById("close-advice-btn");

    alert('hello');

    if (form && formCard && adviceCard) {
        form.addEventListener("submit", function(e) {
            e.preventDefault(); 
            alert('submit here');
            formCard.style.display = "none";
            adviceCard.style.display = "block";
        });
    }

    if (closeBtn && formCard && adviceCard) {
        closeBtn.addEventListener("click", function() {
            adviceCard.style.display = "none";
            formCard.style.display = "block";
        });
    }
});
