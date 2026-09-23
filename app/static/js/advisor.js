/**
 * Financial Advisor — Step 7I Competition Demo Controller
 * 
 * Strict Architecture Boundary:
 * - This file is EXCLUSIVELY an input collector and presentation layer.
 * - Zero financial rule logic, metrics formulas, or decisions are computed here.
 * - All authoritative calculations and decisions come from /api/consult.
 * - Uses safe DOM rendering (textContent) to prevent XSS.
 */

document.addEventListener("DOMContentLoaded", function () {
    const s1 = document.getElementById("advisor-step-1");
    const s2 = document.getElementById("advisor-step-2");
    const l1 = document.getElementById("step-1-indicator");
    const l2 = document.getElementById("step-2-indicator");
    const stepperWrapper = document.getElementById("stepper-wrapper");

    const form = document.getElementById("advisor-form");
    const btnNext = document.getElementById("btn-next");
    const btnBack = document.getElementById("btn-back");
    const btnSubmit = document.getElementById("btn-submit-advisor");
    const btnClose = document.getElementById("btn-close");

    const loadingState = document.getElementById("advisor-loading-state");
    const errorAlert = document.getElementById("advisor-error-alert");
    const errorMessage = document.getElementById("advisor-error-message");
    const errorFieldsList = document.getElementById("advisor-error-fields");
    const resultsContainer = document.getElementById("advisor-results-container");

    const incomeInput = document.getElementById("income");
    const expenseInput = document.getElementById("expense");
    const goalInput = document.getElementById("goal_cost");
    const maritalSelect = document.getElementById("martial_status");

    // =========================================================================
    // 1. Wizard Step Navigation
    // =========================================================================

    function showStep1() {
        if (s1 && s2) {
            s2.classList.add("d-none");
            s1.classList.remove("d-none");
            if (l1 && l2) {
                l2.classList.remove("active");
                l1.classList.add("active");
            }
        }
    }

    function showStep2() {
        if (s1 && s2) {
            s1.classList.add("d-none");
            s2.classList.remove("d-none");
            if (l1 && l2) {
                l1.classList.remove("active");
                l2.classList.add("active");
            }
        }
    }

    btnNext?.addEventListener("click", () => {
        const inputs = s1.querySelectorAll("input, select");
        let valid = true;
        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity();
                valid = false;
            }
        });

        if (valid) {
            showStep2();
        }
    });

    btnBack?.addEventListener("click", () => {
        showStep1();
    });

    // =========================================================================
    // 2. Competition Demo Presets (Populate Inputs Only)
    // =========================================================================

    function setRadioValue(fieldName, targetValue) {
        const radios = document.querySelectorAll(`input[name="${fieldName}"]`);
        radios.forEach(radio => {
            if (radio.value === targetValue) {
                radio.checked = true;
            }
        });
    }

    function getRadioValue(fieldName) {
        const checked = document.querySelector(`input[name="${fieldName}"]:checked`);
        return checked ? checked.value : "";
    }

    const DEMO_PRESETS = {
        "1": {
            // Demo 1: Tight Margin
            income: 1000,
            expense: 900,
            goal: 1000,
            marital: "Single",
            employment: "employed",
            debt: "no debt",
            spending: "average spend"
        },
        "2": {
            // Demo 2: Deficit + Debt
            income: 1000,
            expense: 1200,
            goal: 1000,
            marital: "Single",
            employment: "employed",
            debt: "debt",
            spending: "average spend"
        },
        "3": {
            // Demo 3: Zero Income Safety
            income: 0,
            expense: 500,
            goal: 0,
            marital: "Single",
            employment: "not employed",
            debt: "no debt",
            spending: "average spend"
        },
        "4": {
            // Demo 4: Stable Buffer
            income: 1500,
            expense: 1000,
            goal: 2000,
            marital: "Single",
            employment: "employed",
            debt: "no debt",
            spending: "average spend"
        }
    };

    document.querySelectorAll(".demo-preset-btn").forEach(btn => {
        btn.addEventListener("click", function () {
            const demoId = this.getAttribute("data-demo");
            const preset = DEMO_PRESETS[demoId];
            if (!preset) return;

            // Populate form inputs
            if (incomeInput) incomeInput.value = preset.income;
            if (expenseInput) expenseInput.value = preset.expense;
            if (goalInput) goalInput.value = preset.goal;
            if (maritalSelect) maritalSelect.value = preset.marital;

            setRadioValue("employment_status", preset.employment);
            setRadioValue("debt_status", preset.debt);
            setRadioValue("spending_habit", preset.spending);

            // Hide previous results/errors, advance to Step 2 so user can review & run
            hideError();
            if (resultsContainer) resultsContainer.classList.add("d-none");
            if (form) form.classList.remove("d-none");
            if (stepperWrapper) stepperWrapper.classList.remove("d-none");

            showStep2();
        });
    });



    // =========================================================================
    // 3. Error Handling Helpers
    // =========================================================================

    function showError(message, fields) {
        if (!errorAlert) return;
        if (errorMessage) errorMessage.textContent = message || "An error occurred during evaluation.";
        if (errorFieldsList) {
            errorFieldsList.innerHTML = "";
            if (fields && typeof fields === "object") {
                Object.entries(fields).forEach(([fieldName, fieldMsg]) => {
                    const li = document.createElement("li");
                    li.textContent = `${fieldName}: ${fieldMsg}`;
                    errorFieldsList.appendChild(li);
                });
            }
        }
        errorAlert.classList.remove("d-none");
        errorAlert.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function hideError() {
        if (errorAlert) {
            errorAlert.classList.add("d-none");
            if (errorFieldsList) errorFieldsList.innerHTML = "";
        }
    }

    // =========================================================================
    // 4. Safe Results View Renderer
    // =========================================================================

    function formatCurrency(val) {
        if (val === null || val === undefined) return "$0.00";
        return `$${Number(val).toFixed(2)}`;
    }

    function renderDynamicResults(resData) {
        if (!resultsContainer) return;

        const metrics = resData.metrics || {};
        const decision = resData.decision || {};
        const trace = resData.decision_trace || {};
        const facts = resData.facts || {};

        // Active document language
        const isKm = document.documentElement.lang === "km";
        const conclusionText = isKm ? (resData.conclusion?.km || resData.conclusion?.en) : resData.conclusion?.en;
        const adviceText = isKm ? (resData.advice?.km || resData.advice?.en) : resData.advice?.en;

        resultsContainer.innerHTML = "";

        const card = document.createElement("div");
        card.className = "results-report animate__animated animate__fadeIn";

        // Header banner
        const header = document.createElement("div");
        header.className = "report-header-banner";
        header.innerHTML = `
            <div>
                <h4 class="fw-bold mb-1">${isKm ? "ការវិភាគប្រព័ន្ធអ្នកជំនាញ" : "Expert System Analysis"}</h4>
                <p class="mb-0 small opacity-75">${isKm ? "វដ្តនៃការវិភាគបានបញ្ចប់ // ការវាយតម្លៃវិធានបានពេញលេញ" : "Inference cycle complete // Deterministic rule evaluation"}</p>
            </div>
            <div class="status-badge-white">
                <i class="bi bi-cpu-fill text-info me-1"></i>
                <span id="res-kb-ver">${resData.knowledge_base_version || "financial-kb-v1.0"}</span>
            </div>
        `;
        card.appendChild(header);

        const body = document.createElement("div");
        body.className = "p-4 p-md-5";

        // Row 1: Snapshot grid
        const row1 = document.createElement("div");
        row1.className = "row g-3 mb-4";

        const incomeCol = document.createElement("div");
        incomeCol.className = "col-6 col-md-3";
        incomeCol.innerHTML = `
            <div class="metric-mini-card">
                <span class="label">${isKm ? "ចំណូលប្រចាំខែ" : "Monthly Income"}</span>
                <span class="value text-body d-block">${formatCurrency(metrics.monthly_income)}</span>
            </div>
        `;

        const expenseCol = document.createElement("div");
        expenseCol.className = "col-6 col-md-3";
        expenseCol.innerHTML = `
            <div class="metric-mini-card">
                <span class="label">${isKm ? "ចំណាយប្រចាំខែ" : "Monthly Expense"}</span>
                <span class="value text-body d-block">${formatCurrency(metrics.monthly_expense)}</span>
            </div>
        `;

        const cashflowCol = document.createElement("div");
        cashflowCol.className = "col-6 col-md-3";
        let cashflowHtml = `<span class="value text-secondary d-block">$0.00</span>`;
        if (metrics.net_cashflow > 0) {
            cashflowHtml = `<span class="value text-success d-block">+${formatCurrency(metrics.net_cashflow)}</span>`;
        } else if (metrics.net_cashflow < 0) {
            cashflowHtml = `<span class="value text-danger d-block">-${formatCurrency(Math.abs(metrics.net_cashflow))}</span>`;
        }
        cashflowCol.innerHTML = `
            <div class="metric-mini-card">
                <span class="label">${isKm ? "លំហូរសាច់ប្រាក់សុទ្ធប្រចាំខែ" : "Monthly Net Cash Flow"}</span>
                ${cashflowHtml}
            </div>
        `;

        const horizonCol = document.createElement("div");
        horizonCol.className = "col-6 col-md-3";
        let horizonHtml = `<span class="value text-muted d-block small fs-6 fst-italic">${isKm ? "មិនមាន (ឱនភាព)" : "Unavailable (Deficit)"}</span>`;
        if (metrics.natural_goal_months !== null && metrics.natural_goal_months !== undefined) {
            horizonHtml = `<span class="value text-primary d-block">${Number(metrics.natural_goal_months).toFixed(1)} <small class="fs-6 fw-normal text-muted">${isKm ? "ខែ" : "Months"}</small></span>`;
        }
        horizonCol.innerHTML = `
            <div class="metric-mini-card">
                <span class="label">${isKm ? "រយៈពេលរំពឹងទុក" : "Projected Horizon"}</span>
                ${horizonHtml}
            </div>
        `;

        row1.appendChild(incomeCol);
        row1.appendChild(expenseCol);
        row1.appendChild(cashflowCol);
        row1.appendChild(horizonCol);
        body.appendChild(row1);

        // Row 2: Ratios strip
        const row2 = document.createElement("div");
        row2.className = "row g-3 mb-5";

        const expenseRatioCol = document.createElement("div");
        expenseRatioCol.className = "col-md-6";
        let expRatioHtml = `<span class="value text-muted d-block small fs-6 fst-italic">${isKm ? "មិនមានទេ ព្រោះចំណូលប្រចាំខែស្មើនឹងសូន្យ។" : "Not available because monthly income is zero."}</span>`;
        if (metrics.expense_ratio !== null && metrics.expense_ratio !== undefined) {
            expRatioHtml = `<span class="value text-warning d-block">${(metrics.expense_ratio * 100).toFixed(1)}%</span>`;
        }
        expenseRatioCol.innerHTML = `
            <div class="metric-mini-card">
                <span class="label">${isKm ? "បន្ទុកចំណាយ" : "Expense Load"}</span>
                ${expRatioHtml}
            </div>
        `;

        const surplusRatioCol = document.createElement("div");
        surplusRatioCol.className = "col-md-6";
        let surRatioHtml = `<span class="value text-muted d-block small fs-6 fst-italic">${isKm ? "មិនមានទេ ព្រោះចំណូលប្រចាំខែស្មើនឹងសូន្យ។" : "Not available because monthly income is zero."}</span>`;
        if (metrics.surplus_ratio !== null && metrics.surplus_ratio !== undefined) {
            surRatioHtml = `<span class="value text-success d-block">${(metrics.surplus_ratio * 100).toFixed(1)}%</span>`;
        }
        surplusRatioCol.innerHTML = `
            <div class="metric-mini-card">
                <span class="label">${isKm ? "សក្តានុពលសន្សំ" : "Savings Potential"}</span>
                ${surRatioHtml}
            </div>
        `;

        row2.appendChild(expenseRatioCol);
        row2.appendChild(surplusRatioCol);
        body.appendChild(row2);

        // Decision report
        const reportContent = document.createElement("div");
        reportContent.className = "report-content";

        const titleDiv = document.createElement("div");
        titleDiv.className = "mb-4 text-center";
        const catBadge = document.createElement("span");
        catBadge.className = "badge bg-primary-subtle text-primary rounded-pill px-3 py-1 mb-2 font-monospace small";
        catBadge.textContent = decision.category || "FINANCIAL_CONSULTANT_RECOMMENDATION";
        const heading = document.createElement("h4");
        heading.className = "fw-bold text-body-emphasis";
        heading.textContent = conclusionText || "Financial Advisory Analysis";
        titleDiv.appendChild(catBadge);
        titleDiv.appendChild(heading);
        reportContent.appendChild(titleDiv);

        const caveats = resData.advisory_caveats || [];
        if (caveats.length > 0) {
            const caveatAlert = document.createElement("div");
            caveatAlert.className = "alert alert-warning border rounded-3 p-3 mb-4 small";
            caveatAlert.id = "dynamic-advisory-caveats-box";

            const caveatHeader = document.createElement("div");
            caveatHeader.className = "d-flex align-items-center gap-2 fw-semibold mb-1";
            caveatHeader.innerHTML = `<i class="bi bi-exclamation-triangle-fill text-warning"></i><span>${isKm ? "ការបញ្ជាក់ និងការសន្មត់នៃការប្រឹក្សា" : "Advisory Disclosures & Assumptions"}</span>`;
            caveatAlert.appendChild(caveatHeader);

            const caveatUl = document.createElement("ul");
            caveatUl.className = "mb-0 ps-3";
            caveats.forEach(c => {
                const li = document.createElement("li");
                li.textContent = c;
                caveatUl.appendChild(li);
            });
            caveatAlert.appendChild(caveatUl);
            reportContent.appendChild(caveatAlert);
        }

        const adviceBox = document.createElement("div");
        adviceBox.className = "advice-box mb-4";
        const adviceBoxHeader = document.createElement("div");
        adviceBoxHeader.className = "d-flex align-items-center gap-2 mb-3";
        adviceBoxHeader.innerHTML = `<i class="bi bi-diagram-3-fill text-primary"></i><span class="fw-bold small text-uppercase letter-spacing text-muted">${isKm ? "ផែនការសកម្មភាពដែលបានណែនាំ" : "Prescribed Action Protocol"}</span>`;
        const adviceP = document.createElement("p");
        adviceP.className = "advice-text mb-0";
        adviceP.textContent = adviceText || "No advice available.";
        adviceBox.appendChild(adviceBoxHeader);
        adviceBox.appendChild(adviceP);
        reportContent.appendChild(adviceBox);

        // Certainty Factor Rating
        if (decision.certainty !== undefined && decision.certainty !== null) {
            const certPct = Math.round(Number(decision.certainty) * 100);
            const confSec = document.createElement("div");
            confSec.className = "confidence-section mb-4";
            confSec.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="d-flex align-items-center gap-2">
                        <i class="bi bi-shield-check text-primary fs-5"></i>
                        <span class="small fw-bold text-uppercase text-muted">${isKm ? "កម្រិតនៃភាពប្រាកដប្រជា" : "Certainty Factor"}</span>
                    </div>
                    <span class="badge bg-primary rounded-pill px-3 py-1 fw-bold font-monospace">
                        ${isKm ? `ការផ្គូផ្គង ${certPct}%` : `${certPct}% Match`}
                    </span>
                </div>
                <div class="progress" style="height: 8px; border-radius: 20px; background: rgba(0,0,0,0.08);">
                    <div class="progress-bar confidence-progress-bar" style="width: ${certPct}%;"></div>
                </div>
                <small class="text-muted d-block text-center mt-2 italic">
                    ${isKm ? "កម្រិតប្រាកដប្រជាត្រូវបានកំណត់ដោយការផ្ទៀងផ្ទាត់វិធានអ្នកជំនាញ" : "Certainty factor determined through authoritative expert rule verification"}
                </small>
            `;
            reportContent.appendChild(confSec);
        }

        body.appendChild(reportContent);

        // "Understanding Your Recommendation" Section (plain financial language)
        const explanationText = resData.explanation || trace.selection_reason || "";
        if (explanationText) {
            const explainSec = document.createElement("div");
            explainSec.className = "explainability-section mt-4";

            const explainCard = document.createElement("div");
            explainCard.className = "card border rounded-4 shadow-sm overflow-hidden";
            explainCard.innerHTML = `
                <div class="card-header bg-body-tertiary p-3 border-0 d-flex align-items-center gap-2">
                    <i class="bi bi-lightbulb-fill text-primary"></i>
                    <h6 class="fw-bold text-primary mb-0">${isKm ? "ការយល់ដឹងអំពីអនុសាសន៍របស់អ្នក" : "Understanding Your Recommendation"}</h6>
                </div>
                <div class="card-body p-4 bg-body border-top">
                    <p class="mb-0 text-body fs-6" style="line-height: 1.6;">${explanationText}</p>
                </div>
            `;
            explainSec.appendChild(explainCard);
            body.appendChild(explainSec);
        }

        // Recalibrate Button
        const recalibrateDiv = document.createElement("div");
        recalibrateDiv.className = "text-center mt-5";
        const recalibrateBtn = document.createElement("button");
        recalibrateBtn.className = "btn btn-outline-primary rounded-pill px-4 py-2 fw-semibold";
        recalibrateBtn.type = "button";
        recalibrateBtn.innerHTML = `<i class="bi bi-arrow-repeat me-2"></i>${isKm ? "ដំណើរការឡើងវិញ" : "Recalibrate Inference Scan"}`;
        recalibrateBtn.addEventListener("click", resetToInput);
        recalibrateDiv.appendChild(recalibrateBtn);
        body.appendChild(recalibrateDiv);

        card.appendChild(body);
        resultsContainer.appendChild(card);
        resultsContainer.classList.remove("d-none");
    }

    function resetToInput() {
        if (resultsContainer) resultsContainer.classList.add("d-none");
        hideError();
        if (form) form.classList.remove("d-none");
        if (stepperWrapper) stepperWrapper.classList.remove("d-none");
        showStep1();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    if (btnClose) {
        btnClose.addEventListener("click", resetToInput);
    }

    // =========================================================================
    // 5. AJAX Form Submission to /api/consult
    // =========================================================================

    if (form) {
        form.addEventListener("submit", async function (e) {
            e.preventDefault();
            hideError();

            const income = incomeInput ? incomeInput.value : "";
            const expense = expenseInput ? expenseInput.value : "";
            const goal = goalInput ? goalInput.value : "0";
            const marital = maritalSelect ? maritalSelect.value : "Single";
            const employment = getRadioValue("employment_status");
            const debt = getRadioValue("debt_status");
            const spending = getRadioValue("spending_habit");

            const activeLang = document.documentElement.lang || "en";

            const payload = {
                monthly_income: income !== "" ? parseFloat(income) : null,
                monthly_expense: expense !== "" ? parseFloat(expense) : null,
                goal_cost: goal !== "" ? parseFloat(goal) : 0.0,
                marital_status: marital || "Single",
                language: activeLang
            };
            if (employment !== "") payload.employment_status = employment;
            if (debt !== "") payload.debt_status = debt;
            if (spending !== "") payload.spending_habit = spending;

            // Loading state
            if (loadingState) loadingState.classList.remove("d-none");
            form.classList.add("d-none");
            if (stepperWrapper) stepperWrapper.classList.add("d-none");
            if (btnSubmit) btnSubmit.disabled = true;

            try {
                // Read CSRF token if present
                const csrfMeta = document.querySelector('meta[name="csrf-token"]');
                const csrfInput = document.querySelector('input[name="csrf_token"]');
                const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : (csrfInput ? csrfInput.value : "");

                const reqHeaders = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                };
                if (csrfToken) {
                    reqHeaders["X-CSRFToken"] = csrfToken;
                }

                const response = await fetch("/api/consult", {
                    method: "POST",
                    headers: reqHeaders,
                    credentials: "same-origin",
                    body: JSON.stringify(payload)
                });

                const contentType = response.headers.get("content-type") || "";
                let data = null;
                if (contentType.includes("application/json")) {
                    data = await response.json();
                }

                if (!response.ok || !data || !data.success) {
                    if (loadingState) loadingState.classList.add("d-none");
                    form.classList.remove("d-none");
                    if (stepperWrapper) stepperWrapper.classList.remove("d-none");
                    if (btnSubmit) btnSubmit.disabled = false;

                    const errMsg = (data && data.error && data.error.message)
                        ? data.error.message
                        : `Advisory service returned an error (HTTP ${response.status}).`;
                    const errFields = (data && data.error && data.error.fields) || {};
                    showError(errMsg, errFields);
                    return;
                }

                // Render dynamic results safely
                if (loadingState) loadingState.classList.add("d-none");
                if (btnSubmit) btnSubmit.disabled = false;
                renderDynamicResults(data);
                resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });

            } catch (err) {
                console.error("Advisory consult request error:", err);
                if (loadingState) loadingState.classList.add("d-none");
                form.classList.remove("d-none");
                if (stepperWrapper) stepperWrapper.classList.remove("d-none");
                if (btnSubmit) btnSubmit.disabled = false;

                showError("Unable to connect to advisory service. Please check your network connection.", {});
            }
        });
    }
});
