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

function goalCard(goal, index, custom = false) {
  const enabled = custom || ['Marriage', 'Home', 'Car / Bike'].includes(goal.name);
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
    </div></article>`;
}

function connectGoalCard(card) {
  const toggle = card.querySelector('.goal-enabled');
  const toggleText = card.querySelector('.toggle b');
  const range = card.querySelector('.goal-years');
  const number = card.querySelector('.goal-years-number');
  const output = card.querySelector('.years-output');
  const syncYears = (value) => { range.value = value; number.value = value; output.textContent = `${value} years`; };
  range.addEventListener('input', () => syncYears(range.value));
  number.addEventListener('input', () => { if (number.value) syncYears(number.value); });
  toggle.addEventListener('change', () => { card.classList.toggle('is-enabled', toggle.checked); toggleText.textContent = toggle.checked ? 'Planned' : 'Paused'; });
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
  }));
}

function renderGoalCards(goals) {
  goalResults.innerHTML = goals.map((goal) => `<article class="result-card">
    <h3>${goal.name}</h3><span>Current estimated cost</span><strong>${money.format(goal.current_cost)}</strong>
    <span>Projected cost</span><strong>${money.format(goal.future_cost)}</strong>
    <span>${goal.frequency === 'yearly' ? 'Yearly contribution' : 'Monthly contribution'}</span><strong class="sip">${money.format(goal.contribution_amount)}</strong>
  </article>`).join('');
}

function renderAnalysis(analysis) {
  document.querySelector('#analysis-status').textContent = analysis.status;
  document.querySelector('#required-total').textContent = money.format(analysis.total_required);
  document.querySelector('#monthly-capacity').textContent = money.format(analysis.monthly_capacity);
  const difference = analysis.shortfall > 0 ? analysis.shortfall : analysis.surplus;
  document.querySelector('#difference').textContent = `${analysis.shortfall > 0 ? '-' : '+'}${money.format(difference)}`;
  document.querySelector('#recommendation').textContent = analysis.recommendation;
}

function renderSuggestionPlan(plan) {
  document.querySelector('#priority-goal').textContent = `Start with ${plan.priority_goal}`;
  document.querySelector('#priority-focus').textContent = plan.focus;
  document.querySelector('#priority-action').textContent = plan.action;
  document.querySelector('#horizon-note').textContent = plan.horizon_note;
  document.querySelector('#suggestion-steps').innerHTML = plan.steps.map((step) => `<li>${step}</li>`).join('');
  investmentState = plan.investment_options.map((option) => ({ ...option, selected_monthly: option.monthly_amount }));
  document.querySelector('#investment-options').innerHTML = investmentState.map((option, index) => `
    <article class="investment-card" data-investment-index="${index}"><h3>${option.name}</h3><span>${option.fit}</span><strong>${option.risk} risk</strong><div class="option-amounts"><b class="option-monthly">${money.format(option.monthly_amount)}<small>/ month</small></b><b class="option-yearly">${money.format(option.yearly_amount)}<small>/ year</small></b></div><div class="amount-adjuster"><button class="amount-step" data-change="-1" type="button" aria-label="Decrease ${option.name} amount">−</button><input class="amount-slider" type="range" min="${Math.max(100, Math.round(option.monthly_amount * 0.25))}" max="${Math.round(option.monthly_amount * 3)}" step="100" value="${option.monthly_amount}" aria-label="Monthly ${option.name} investment"><button class="amount-step" data-change="1" type="button" aria-label="Increase ${option.name} amount">+</button></div><p class="option-projection"></p><p>${option.note}</p></article>
  `).join('');
  document.querySelectorAll('.investment-card').forEach((card) => {
    card.querySelector('.amount-slider').addEventListener('input', (event) => updateInvestmentOption(card, Number(event.target.value)));
    card.querySelectorAll('.amount-step').forEach((button) => button.addEventListener('click', () => {
      const slider = card.querySelector('.amount-slider');
      updateInvestmentOption(card, Number(slider.value) + Number(button.dataset.change) * Number(slider.step));
    }));
    updateInvestmentOption(card, Number(card.querySelector('.amount-slider').value));
  });
  const insight = document.querySelector('#model-insight');
  const insightText = document.querySelector('#model-insight-text');
  insight.hidden = false;
  insightText.textContent = plan.model_insight.available
    ? `The ${plan.model_insight.model} model estimates ${money.format(plan.model_insight.predicted_monthly_salary)} per month from the optional profile. This is a benchmark only; the planner always uses your entered salary.`
    : plan.model_insight.message;
}

function updateInvestmentOption(card, amount) {
  const index = Number(card.dataset.investmentIndex);
  const option = investmentState[index];
  const slider = card.querySelector('.amount-slider');
  slider.value = Math.max(Number(slider.min), Math.min(Number(slider.max), amount));
  option.selected_monthly = Number(slider.value);
  const rate = option.annual_return / 100 / 12;
  const months = option.years * 12;
  const projectedValue = option.selected_monthly * (((1 + rate) ** months - 1) / rate);
  const yearly = option.selected_monthly * 12;
  const gap = option.goal_amount - projectedValue;
  card.querySelector('.option-monthly').innerHTML = `${money.format(option.selected_monthly)}<small>/ month</small>`;
  card.querySelector('.option-yearly').innerHTML = `${money.format(yearly)}<small>/ year</small>`;
  card.querySelector('.option-projection').textContent = gap > 0
    ? `Projected value ${money.format(projectedValue)} • Gap ${money.format(gap)}`
    : `Projected value ${money.format(projectedValue)} • Surplus ${money.format(Math.abs(gap))}`;
  updateInvestmentTotals();
}

function updateInvestmentTotals() {
  const monthly = investmentState.reduce((total, option) => total + option.selected_monthly, 0);
  const projected = investmentState.reduce((total, option) => {
    const rate = option.annual_return / 100 / 12;
    return total + option.selected_monthly * (((1 + rate) ** (option.years * 12) - 1) / rate);
  }, 0);
  document.querySelector('#investment-total-monthly').textContent = `${money.format(monthly)} / month`;
  document.querySelector('#investment-total-projected').textContent = money.format(projected);
  const amounts = investmentState.map((option) => option.selected_monthly);
  const periods = investmentState.map((option) => option.years);
  document.querySelector('#investment-total-min').textContent = `${money.format(Math.min(...amounts))} / month`;
  document.querySelector('#investment-total-max').textContent = `${money.format(Math.max(...amounts))} / month`;
  document.querySelector('#investment-total-period').textContent = `${Math.min(...periods)}–${Math.max(...periods)} years`;
  document.querySelector('#investment-total-note').textContent = 'Minimum and maximum are alternative option scenarios. The total assumes the selected amount is allocated to every card; compare options individually before investing.';
}

function showError(data) {
  return Array.isArray(data.errors) ? data.errors.map((error) => `${error.field}: ${error.message}`).join(' ') : (data.detail || 'Could not build your plan.');
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';
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
    latestPlan = data; renderGoalCards(data.goals); renderAnalysis(data.analysis); renderSuggestionPlan(data.suggestion_plan); results.hidden = false; results.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
