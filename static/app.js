const form = document.querySelector('#planner-form');
const results = document.querySelector('#results');
const message = document.querySelector('#form-message');
const goalResults = document.querySelector('#goal-results');
const goalOptions = document.querySelector('#goal-options');
const resetButton = document.querySelector('#reset-button');
const downloadButton = document.querySelector('#download-button');
const addGoalButton = document.querySelector('#add-goal-button');
const customGoals = document.querySelector('#custom-goals');
const citySelect = document.querySelector('select[name="city"]');
const inflationRate = document.querySelector('#inflation-rate');
const annualReturn = document.querySelector('#annual-return');

const money = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 });
let latestPlan = null;
let customGoalCount = 0;
let investmentState = [];

function setText(selector, value) {
  const element = document.querySelector(selector);
  if (element) element.textContent = value;
}

function goalCard(goal, index, custom = false) {
  const enabled = custom || ['Marriage', 'Home', 'Car / Bike'].includes(goal.name);
  const isVehicle = goal.name === 'Car / Bike';
  const id = `${custom ? 'custom' : 'default'}-${index}`;
  const years = custom ? 5 : (goal.name === 'Emergency Fund' ? 1 : goal.name === 'Vacation / Trip' ? 3 : goal.name === 'Marriage' ? 5 : goal.name === 'Car / Bike' ? 4 : 10);
  return `<article class="configurable-goal ${custom ? 'custom-goal-card' : ''} ${enabled ? 'is-enabled' : ''}" data-goal-id="${id}">
    <div class="goal-card-top"><div><span class="goal-icon">${String(index + 1).padStart(2, '0')}</span><h4>${goal.name}</h4></div>
      <label class="toggle"><input class="goal-enabled" type="checkbox" ${enabled ? 'checked' : ''}><span></span><b>${enabled ? 'Planned' : 'Paused'}</b></label></div>
    <div class="goal-controls">
      <label>Current estimated cost <small>INR</small><input class="goal-cost" type="number" min="1000" max="1000000000" step="1000" inputmode="numeric" value="${goal.current_cost}" required></label>
      <label>Timeline <output class="years-output">${years} years</output><input class="goal-years" type="range" min="1" max="60" value="${years}"><input class="goal-years-number" type="number" min="1" max="60" value="${years}"></label>
      <fieldset><legend>Contribution frequency</legend><label><input class="frequency" type="radio" name="frequency-${id}" value="monthly" checked> Monthly</label><label><input class="frequency" type="radio" name="frequency-${id}" value="yearly"> Yearly</label></fieldset>
      ${custom ? '<button class="remove-goal" type="button" aria-label="Remove custom goal">&times;</button>' : ''}
    </div>${isVehicle ? `<div class="vehicle-finance"><div class="vehicle-finance-heading"><strong>Vehicle EMI</strong><label class="toggle"><input class="emi-enabled" type="checkbox" checked><span></span><b>On</b></label></div><div class="vehicle-finance-controls"><label>Down payment <output class="down-payment-output">80%</output><input class="down-payment" type="range" min="0" max="100" step="1" value="80"></label><span class="vehicle-tenure">Tenure: ${years} years</span></div><div class="vehicle-finance-preview"><span>Down payment needed <strong class="down-payment-amount"></strong></span><span>Loan amount <strong class="loan-amount"></strong></span><span>EMI per month <strong class="emi-amount"></strong></span></div></div>` : ''}</article>`;
}

function connectGoalCard(card) {
  const toggle = card.querySelector('.goal-enabled');
  const toggleText = card.querySelector('.toggle b');
  const range = card.querySelector('.goal-years');
  const number = card.querySelector('.goal-years-number');
  const output = card.querySelector('.years-output');
  const vehicle = card.querySelector('.vehicle-finance');
  const syncVehiclePreview = () => {
    if (!vehicle) return;
    const cost = Number(card.querySelector('.goal-cost').value) || 0;
    const years = Number(number.value) || 1;
    const downPercentage = Number(vehicle.querySelector('.down-payment').value);
    const futureCost = cost * (1 + Number(inflationRate.value) / 100) ** years;
    const loanAmount = futureCost * (100 - downPercentage) / 100;
    const months = years * 12;
    const loanRate = 10 / 100 / 12;
    const emi = loanAmount === 0 ? 0 : (loanAmount * loanRate * (1 + loanRate) ** months) / ((1 + loanRate) ** months - 1);
    vehicle.querySelector('.down-payment-output').textContent = `${downPercentage}%`;
    vehicle.querySelector('.vehicle-tenure').textContent = `Tenure: ${years} years`;
    vehicle.querySelector('.down-payment-amount').textContent = money.format(futureCost * downPercentage / 100);
    vehicle.querySelector('.loan-amount').textContent = money.format(loanAmount);
    vehicle.querySelector('.emi-amount').textContent = vehicle.querySelector('.emi-enabled').checked ? money.format(emi) : 'Off';
  };
  const syncYears = (value) => { range.value = value; number.value = value; output.textContent = `${value} years`; syncVehiclePreview(); };
  range.addEventListener('input', () => syncYears(range.value));
  number.addEventListener('input', () => { if (number.value) syncYears(number.value); });
  toggle.addEventListener('change', () => { card.classList.toggle('is-enabled', toggle.checked); toggleText.textContent = toggle.checked ? 'Planned' : 'Paused'; });
  card.querySelector('.goal-cost').addEventListener('input', syncVehiclePreview);
  vehicle?.querySelector('.down-payment').addEventListener('input', syncVehiclePreview);
  vehicle?.querySelector('.emi-enabled').addEventListener('change', (event) => {
    vehicle.querySelector('.emi-enabled + span + b').textContent = event.target.checked ? 'On' : 'Off';
    syncVehiclePreview();
  });
  syncVehiclePreview();
  card.querySelector('.remove-goal')?.addEventListener('click', () => card.remove());
}

async function loadGoalOptions() {
  if (!citySelect.value) return;
  const response = await fetch(`/api/v1/default-goals?city=${encodeURIComponent(citySelect.value)}`);
  if (!response.ok) throw new Error('Could not load goal options for this city.');
  const goals = await response.json();
  goalOptions.innerHTML = goals.map((goal, index) => goalCard(goal, index)).join('');
  goalOptions.querySelectorAll('.configurable-goal').forEach(connectGoalCard);
}

function addCustomGoal() {
  if (customGoalCount >= 8) {
    message.textContent = 'You can add up to 8 custom goals.';
    return;
  }
  customGoalCount += 1;
  const goal = { name: `Custom goal ${customGoalCount}`, current_cost: 100000 };
  customGoals.insertAdjacentHTML('beforeend', goalCard(goal, customGoalCount + 4, true));
  const card = customGoals.lastElementChild;
  card.querySelector('h4').contentEditable = 'true';
  card.querySelector('h4').title = 'Click to rename';
  connectGoalCard(card);
}

function collectGoals() {
  return [...document.querySelectorAll('.configurable-goal.is-enabled')].map((card) => ({
    name: card.querySelector('h4').textContent.trim(),
    current_cost: Number(card.querySelector('.goal-cost').value),
    years: Number(card.querySelector('.goal-years-number').value),
    frequency: card.querySelector('.frequency:checked').value,
    emi_enabled: card.querySelector('.emi-enabled')?.checked ?? false,
    down_payment_percentage: Number(card.querySelector('.down-payment')?.value ?? 80),
  }));
}

function renderGoalCards(goals) {
  goalResults.innerHTML = goals.map((goal) => `<article class="result-card ${goal.name === 'Car / Bike' ? 'car' : goal.name === 'Home' ? 'home' : ''}">
    <h3>${goal.name}</h3><span>Current estimated cost</span><strong>${money.format(goal.current_cost)}</strong>
    <span>Projected cost</span><strong>${money.format(goal.future_cost)}</strong>
    ${goal.emi_enabled ? `<span>Upfront contribution (${goal.down_payment_percentage}%)</span><strong>${money.format(goal.down_payment_amount)}</strong><span>Loan amount (${goal.loan_percentage}%)</span><strong>${money.format(goal.loan_amount)}</strong><span>Vehicle EMI (${goal.loan_term_years} years at ${goal.loan_interest_rate}%)</span><strong>${money.format(goal.emi)}</strong><span>Monthly total: savings + EMI</span><strong class="sip">${money.format(goal.monthly_total)}</strong>` : `<span>Down payment (${goal.down_payment_percentage}%)</span><strong>${money.format(goal.down_payment_amount)}</strong><span>EMI</span><strong>Off</strong><span>Monthly savings for down payment</span><strong class="sip">${money.format(goal.monthly_sip)}</strong>`}
  </article>`).join('');
}

function renderAnalysis(analysis) {
  document.querySelector('#analysis-status').textContent = analysis.status;
  document.querySelector('#required-total').textContent = money.format(analysis.total_required);
  document.querySelector('#monthly-capacity').textContent = money.format(analysis.monthly_capacity_after_emi);
  setText('#monthly-emi', money.format(analysis.monthly_emi));
  const difference = analysis.shortfall > 0 ? analysis.shortfall : analysis.surplus;
  document.querySelector('#difference').textContent = `${analysis.shortfall > 0 ? '-' : '+'}${money.format(difference)}`;
  document.querySelector('#recommendation').textContent = analysis.recommendation;
}

function renderSuggestionPlan(plan, profile, analysis) {
  document.querySelector('#priority-goal').textContent = `Start with ${plan.priority_goal}`;
  document.querySelector('#priority-focus').textContent = plan.focus;
  document.querySelector('#priority-action').textContent = plan.action;
  document.querySelector('#horizon-note').textContent = plan.horizon_note;
  document.querySelector('#suggestion-steps').innerHTML = plan.steps.map((step) => `<li>${step}</li>`).join('');
  investmentState = plan.investment_options.map((option) => ({ ...option, selected_monthly: option.monthly_amount }));
  const portfolioMonthly = Math.min(analysis.total_required, analysis.monthly_capacity);
  document.querySelector('#investment-options').innerHTML = `<div class="portfolio-adjuster"><label>Monthly investment toward goals <output id="portfolio-monthly-output">${money.format(portfolioMonthly)}</output><input id="portfolio-monthly-slider" type="range" min="${Math.max(100, Math.round(portfolioMonthly * 0.25))}" max="${Math.round(Math.max(portfolioMonthly * 3, analysis.monthly_capacity))}" step="100" value="${portfolioMonthly}"></label><p>Split equally across ${investmentState.length} categories: <strong id="portfolio-share-output"></strong> per category each month.</p></div>${investmentState.map((option) => `
    <article class="investment-card"><h3>${option.name}</h3><span>${option.fit}</span><strong>${option.risk} risk</strong><div class="option-amounts"><b class="option-monthly">${money.format(option.monthly_amount)}<small>/ month</small></b><b class="option-yearly">${money.format(option.yearly_amount)}<small>/ year</small></b></div><p class="option-projection"></p><p>${option.note}</p></article>
  `).join('')}`;
  document.querySelector('#portfolio-monthly-slider').addEventListener('input', (event) => updateInvestmentPortfolio(Number(event.target.value), analysis.monthly_capacity));
  updateInvestmentPortfolio(portfolioMonthly, analysis.monthly_capacity);
  const insight = document.querySelector('#model-insight');
  const insightText = document.querySelector('#model-insight-text');
  if (insight) insight.hidden = false;
  setText('#entered-salary', money.format(profile.monthly_salary_entered));
  setText('#predicted-salary', profile.monthly_salary_predicted === null
    ? 'Unavailable'
    : money.format(profile.monthly_salary_predicted));
  if (insightText) insightText.textContent = plan.model_insight.available
    ? `Expected salary calculated from your city, education, job role, and ${profile.experience_level} experience level using the ${plan.model_insight.model} model. Your real salary remains the amount used for goal affordability.`
    : plan.model_insight.message;
}

function updateInvestmentPortfolio(totalMonthly, monthlyCapacity) {
  const share = totalMonthly / investmentState.length;
  investmentState.forEach((option) => { option.selected_monthly = share; });
  document.querySelector('#portfolio-monthly-output').textContent = money.format(totalMonthly);
  document.querySelector('#portfolio-share-output').textContent = money.format(share);
  document.querySelectorAll('.investment-card').forEach((card, index) => {
    const option = investmentState[index];
    const rate = option.annual_return / 100 / 12;
    const months = option.years * 12;
    const projectedValue = option.selected_monthly * (((1 + rate) ** months - 1) / rate);
    const gap = option.goal_amount - projectedValue;
    card.querySelector('.option-monthly').innerHTML = `${money.format(option.selected_monthly)}<small>/ month</small>`;
    card.querySelector('.option-yearly').innerHTML = `${money.format(option.selected_monthly * 12)}<small>/ year</small>`;
    card.querySelector('.option-projection').textContent = gap > 0
      ? `Projected value ${money.format(projectedValue)} • Gap ${money.format(gap)}`
      : `Projected value ${money.format(projectedValue)} • Surplus ${money.format(Math.abs(gap))}`;
  });
  updateInvestmentTotals(monthlyCapacity);
}

function updateInvestmentTotals(monthlyCapacity) {
  const monthly = investmentState.reduce((total, option) => total + option.selected_monthly, 0);
  const projected = investmentState.reduce((total, option) => {
    const rate = option.annual_return / 100 / 12;
    return total + option.selected_monthly * (((1 + rate) ** (option.years * 12) - 1) / rate);
  }, 0);
  setText('#investment-total-monthly', `${money.format(monthly)} / month`);
  setText('#investment-capacity', `${money.format(monthlyCapacity)} / month`);
  const retainedSavings = monthlyCapacity - monthly;
  setText('#investment-savings', retainedSavings >= 0
    ? `${money.format(retainedSavings)} / month`
    : `${money.format(Math.abs(retainedSavings))} shortfall`);
  setText('#investment-total-projected', money.format(projected));
  const amounts = investmentState.map((option) => option.selected_monthly);
  const periods = investmentState.map((option) => option.years);
  setText('#investment-total-min', `${money.format(Math.min(...amounts))} / month`);
  setText('#investment-total-period', `${Math.min(...periods)}–${Math.max(...periods)} years`);
  setText('#investment-total-note', retainedSavings > 0
    ? `Your affordable investment is split equally across all ${investmentState.length} categories. The remaining capacity stays in savings.`
    : `The investment uses your full monthly capacity. Increase savings, reduce the goal amount, or extend the timeline to create a buffer.`);
}

function showError(data) {
  return Array.isArray(data.errors) ? data.errors.map((error) => `${error.field}: ${error.message}`).join(' ') : (data.detail || 'Could not build your plan.');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  const goals = collectGoals();
  if (!goals.length) { message.textContent = 'Turn on at least one goal before calculating.'; return; }
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.querySelector('span:first-child').textContent = 'Calculating...';
  const values = Object.fromEntries(new FormData(form).entries());
  values.age = Number(values.age); values.salary = Number(values.salary); values.saving_percentage = Number(values.saving_percentage); values.inflation_rate = Number(values.inflation_rate); values.annual_return = Number(values.annual_return); values.goals = goals;
  try {
    const response = await fetch('/api/v1/plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(values) });
    const data = await response.json();
    if (!response.ok) throw new Error(showError(data));
    latestPlan = data; renderGoalCards(data.goals); renderAnalysis(data.analysis); renderSuggestionPlan(data.suggestion_plan, { ...data.calculation_profile, experience_level: data.experience_level }, data.analysis); results.hidden = false; results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) { message.textContent = error.message; }
  finally { button.disabled = false; button.querySelector('span:first-child').textContent = 'Build my plan'; }
});

citySelect.addEventListener('change', () => loadGoalOptions().catch((error) => { message.textContent = error.message; }));
addGoalButton.addEventListener('click', addCustomGoal);
resetButton.addEventListener('click', () => { results.hidden = true; window.scrollTo({ top: 0, behavior: 'smooth' }); });
downloadButton.addEventListener('click', () => { if (!latestPlan) return; const url = URL.createObjectURL(new Blob([JSON.stringify(latestPlan, null, 2)], { type: 'application/json' })); const link = document.createElement('a'); link.href = url; link.download = 'financial-dream-plan.json'; link.click(); URL.revokeObjectURL(url); });

loadGoalOptions().catch((error) => { goalOptions.innerHTML = ''; message.textContent = error.message; });

function syncAssumption(slider, output) {
  output.textContent = `${slider.value}%`;
}

inflationRate.addEventListener('input', () => syncAssumption(inflationRate, document.querySelector('#inflation-output')));
annualReturn.addEventListener('input', () => syncAssumption(annualReturn, document.querySelector('#return-output')));
