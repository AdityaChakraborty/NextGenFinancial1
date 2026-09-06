const form = document.querySelector('#planner-form');
const results = document.querySelector('#results');
const message = document.querySelector('#form-message');
const goalResults = document.querySelector('#goal-results');
const resetButton = document.querySelector('#reset-button');

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

  try {
    const response = await fetch('/api/v1/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Could not build your plan.');
    renderGoalCards(data.goals);
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

resetButton.addEventListener('click', () => {
  results.hidden = true;
  window.scrollTo({ top: 0, behavior: 'smooth' });
});
