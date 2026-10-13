document.querySelector('#check').addEventListener('submit', async (event) => {
  event.preventDefault();
  const output = document.querySelector('#result');
  const button = event.target.querySelector('button');
  const values = Object.fromEntries([...event.target.querySelectorAll('input')].map(input => [input.name, input.checked]));
  button.disabled = true;
  output.textContent = 'Checking…';
  try {
    const response = await fetch('/api/check', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(values)});
    if (!response.ok) throw new Error('Request failed');
    const result = await response.json();
    output.textContent = result.ready ? '4 of 4 controls checked. Ready for your release review.' : `${result.passed} of 4 controls checked. Complete the remaining controls before review.`;
  } catch {
    output.textContent = 'The check could not finish. Try again.';
  } finally { button.disabled = false; }
});
