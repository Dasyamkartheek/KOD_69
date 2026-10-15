(() => {
  const workspace = document.querySelector('[data-ide]');
  if (!workspace) return;

  const textarea = workspace.querySelector('#source_code');
  const runButton = workspace.querySelector('[data-run-tests]');
  const resetButton = workspace.querySelector('[data-reset-editor]');
  const status = workspace.querySelector('[data-runtime-status]');
  const summary = workspace.querySelector('[data-result-summary]');
  const resultsContainer = workspace.querySelector('[data-test-results]');
  const testCases = JSON.parse(document.getElementById('challenge-test-cases-data').textContent);
  const starterCode = '# Write your Python solution here';
  let editor = null;
  let worker = null;
  let workerReady = false;
  let pendingSource = null;
  let executionTimer = null;
  let startupTimer = null;

  const normalize = (text) => text.replace(/\r\n/g, '\n').trim();

  function showMessage(message, className = 'small text-secondary') {
    resultsContainer.replaceChildren();
    const paragraph = document.createElement('p');
    paragraph.className = className;
    paragraph.textContent = message;
    resultsContainer.append(paragraph);
  }

  function showResults(results) {
    resultsContainer.replaceChildren();
    let passed = 0;
    for (const result of results) {
      const isPassed = !result.error && normalize(result.output) === normalize(result.expected);
      if (isPassed) passed += 1;
      const card = document.createElement('article');
      card.className = `ide-case-result ${isPassed ? 'is-passed' : 'is-failed'}`;
      const heading = document.createElement('div');
      heading.className = 'd-flex justify-content-between gap-2';
      const name = document.createElement('strong');
      name.textContent = result.name;
      const verdict = document.createElement('span');
      verdict.textContent = isPassed ? 'Passed' : 'Failed';
      heading.append(name, verdict);
      card.append(heading);
      if (result.error) {
        const error = document.createElement('pre');
        error.className = 'ide-output-error';
        error.textContent = result.error;
        card.append(error);
      }
      const output = document.createElement('pre');
      output.className = 'ide-output';
      output.textContent = result.output || '(no output)';
      card.append(output);
      resultsContainer.append(card);
    }
    summary.textContent = `${passed} / ${results.length} passed`;
    summary.className = `small fw-bold ${passed === results.length ? 'text-success' : 'text-danger'}`;
  }

  function finishWithError(message) {
    clearTimeout(executionTimer);
    clearTimeout(startupTimer);
    if (worker) worker.terminate();
    worker = null;
    workerReady = false;
    pendingSource = null;
    runButton.disabled = testCases.length === 0;
    status.textContent = 'Runtime stopped';
    showMessage(message, 'small text-danger mb-0');
    summary.textContent = 'Run failed';
  }

  function sendPendingRun() {
    if (!workerReady || pendingSource === null) return;
    clearTimeout(startupTimer);
    status.textContent = 'Running test cases…';
    executionTimer = setTimeout(() => {
      finishWithError('Execution exceeded 8 seconds and was stopped. Check for an infinite loop.');
    }, 8000);
    worker.postMessage({ type: 'run', source: pendingSource, testCases });
    pendingSource = null;
  }

  function createWorker() {
    if (worker) return;
    try {
      worker = new Worker(workspace.dataset.workerUrl);
      worker.addEventListener('message', (event) => {
        if (event.data.type === 'ready') {
          workerReady = true;
          status.textContent = 'Python runtime ready';
          sendPendingRun();
        } else if (event.data.type === 'results') {
          clearTimeout(executionTimer);
          runButton.disabled = false;
          status.textContent = 'Run complete';
          showResults(event.data.results);
        } else if (event.data.type === 'error') {
          finishWithError(event.data.message);
        }
      });
      worker.addEventListener('error', (event) => {
        finishWithError(event.message || 'Could not start the browser Python runtime.');
      });
      startupTimer = setTimeout(() => {
        finishWithError('Python runtime did not load. Check your connection and try again.');
      }, 60000);
    } catch (error) {
      finishWithError('Your browser could not start the isolated Python runtime.');
    }
  }

  function runTests() {
    const source = editor ? editor.getValue() : textarea.value;
    if (!source.trim()) {
      showMessage('Write some Python code before running tests.');
      return;
    }
    if (!testCases.length) return;
    runButton.disabled = true;
    summary.textContent = 'Running';
    showMessage('Loading the Python runtime in your browser…');
    pendingSource = source;
    if (workerReady) sendPendingRun();
    else createWorker();
  }

  if (window.CodeMirror) {
    editor = window.CodeMirror.fromTextArea(textarea, {
      mode: 'python',
      theme: 'material-darker',
      lineNumbers: true,
      indentUnit: 4,
      tabSize: 4,
      lineWrapping: true,
      extraKeys: {'Ctrl-Enter': runTests, 'Cmd-Enter': runTests},
    });
    editor.setSize('100%', 420);
  }

  runButton.addEventListener('click', runTests);
  resetButton.addEventListener('click', () => {
    if (editor) editor.setValue(starterCode);
    else textarea.value = starterCode;
    summary.textContent = 'Not run';
    summary.className = 'small text-secondary';
    showMessage('Editor reset. Run your code against the challenge tests before submitting.');
  });
})();