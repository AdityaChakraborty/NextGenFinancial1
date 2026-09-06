const form = document.querySelector('#planner-form');
const results = document.querySelector('#results');
const message = document.querySelector('#form-message');
const goalResults = document.querySelector('#goal-results');
const resetButton = document.querySelector('#reset-button');
const downloadButton = document.querySelector('#download-button');
const addGoalButton = document.querySelector('#add-goal-button');
const customGoals = document.querySelector('#custom-goals');
let latestPlan = null;

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const labels = {
  marriage: 'Marriage',
  car: 'Car',
  home: 'Home',
};

let customGoalCount = 0;

function addCustomGoal() {
  customGoalCount += 1;
  const row = document.createElement('div');
  row.className = 'custom-goal-row';
  row.dataset.goalId = customGoalCount;
  row.innerHTML = `
    <label><span>Goal name</span><input name="custom_name_${customGoalCount}" type="text" maxlength="60" placeholder="e.g. Education" required></label>
    <label><span>Current cost <small>INR</small></span><input name="custom_cost_${customGoalCount}" type="number" min="1000" step="1000" placeholder="500000" required></label>
    <label><span>Timeline</span><span class="inline-input"><input name="custom_years_${customGoalCount}" type="number" min="1" max="60" value="5" required><small>years</small></span></label>
    <button class="remove-goal" type="button" aria-label="Remove custom goal">&times;</button>
  `;
  row.querySelector('.remove-goal').addEventListener('click', () => row.remove());
  customGoals.append(row);
}

function renderGoalCards(goals) {
  goalResults.innerHTML = Object.entries(goals).map(([key, goal]) => `
    <article class="result-card ${key}">
      <h3>${labels[key]}</h3>
      <span>Current estimated cost</span>
      <strong>${money.format(goal.current_cost)}</strong>
      <span>Projected cost</span>
      <strong>${money.format(goal.future_cost)}</strong>
      <span>Monthly investment</span>
      <strong class="sip">${money.format(goal.monthly_sip)}</strong>
    </article>
  `).join('');
}

function renderAnalysis(analysis) {
  document.querySelector('#analysis-status').textContent = analysis.status;
  document.querySelector('#required-total').textContent = money.format(analysis.total_required);
  document.querySelector('#monthly-capacity').textContent = money.format(analysis.monthly_capacity);
  const difference = analysis.shortfall > 0 ? analysis.shortfall : analysis.surplus;
  document.querySelector('#difference').textContent = `${analysis.shortfall > 0 ? '-' : '+'}${money.format(difference)}`;
  document.querySelector('#recommendation').textContent = analysis.recommendation;
}

function showError(data) {
  if (Array.isArray(data.errors)) {
    return data.errors.map((error) => `${error.field}: ${error.message}`).join(' ');
  }
  return data.detail || 'Could not build your plan.';
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  message.textContent = '';
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.querySelector('span:first-child').textContent = 'Calculating...';

  const values = Object.fromEntries(new FormData(form).entries());
  ['age', 'salary', 'saving_percentage', 'years_to_marriage', 'years_to_car', 'years_to_home']
    .forEach((key) => { values[key] = Number(values[key]); });
  values.custom_goals = [...customGoals.querySelectorAll('.custom-goal-row')].map((row) => ({
    name: row.querySelector('input[name^="custom_name_"]').value,
    current_cost: Number(row.querySelector('input[name^="custom_cost_"]').value),
    years: Number(row.querySelector('input[name^="custom_years_"]').value),
  }));

  try {
    const response = await fetch('/api/v1/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(showError(data));
    latestPlan = data;
    renderGoalCards(data.goals);
    renderCustomGoalCards(data.custom_goals);
    renderAnalysis(data.analysis);
    results.hidden = false;
    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
    button.querySelector('span:first-child').textContent = 'Build my plan';
  }
});

function renderCustomGoalCards(goals) {
  goals.forEach((goal) => {
    goalResults.insertAdjacentHTML('beforeend', `
      <article class="result-card custom">
        <h3>${goal.name}</h3>
        <span>Current estimated cost</span><strong>${money.format(goal.current_cost)}</strong>
        <span>Projected cost</span><strong>${money.format(goal.future_cost)}</strong>
        <span>Monthly investment</span><strong class="sip">${money.format(goal.monthly_sip)}</strong>
      </article>
    `);
  });
}

resetButton.addEventListener('click', () => {
  results.hidden = true;
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

downloadButton.addEventListener('click', () => {
  if (!latestPlan) return;
  const file = new Blob([JSON.stringify(latestPlan, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(file);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'financial-dream-plan.json';
  link.click();
  URL.revokeObjectURL(url);
});

addGoalButton.addEventListener('click', addCustomGoal);

fetch('/api/v1/cities')
  .then((response) => response.ok ? response.json() : Promise.reject(new Error('Cities unavailable')))
  .then((cities) => {
    const citySelect = document.querySelector('select[name="city"]');
    citySelect.innerHTML = '<option value="" selected disabled>Choose a city</option>';
    cities.forEach((city) => citySelect.add(new Option(city, city)));
  })
  .catch(() => {
    message.textContent = 'Could not load cities. Please restart the local server.';
  });
