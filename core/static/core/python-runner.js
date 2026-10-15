importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');

const runtimePromise = loadPyodide({
  indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/',
}).then((pyodide) => {
  pyodide.runPython(`
import contextlib
import io
import json
import sys

def _codearena_run(source, input_data):
    output = io.StringIO()
    errors = io.StringIO()
    original_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(input_data)
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            exec(compile(source, '<student-code>', 'exec'), {'__name__': '__main__'})
        return json.dumps({'output': output.getvalue(), 'error': errors.getvalue() or None})
    except BaseException as error:
        return json.dumps({
            'output': output.getvalue(),
            'error': f'{type(error).__name__}: {error}',
        })
    finally:
        sys.stdin = original_stdin
`);
  self.postMessage({ type: 'ready' });
  return pyodide;
}).catch((error) => {
  self.postMessage({ type: 'error', message: `Python runtime failed to load: ${error.message}` });
  return null;
});

self.addEventListener('message', async (event) => {
  if (event.data.type !== 'run') return;
  try {
    const pyodide = await runtimePromise;
    if (!pyodide) return;
    const results = [];
    for (const testCase of event.data.testCases) {
      pyodide.globals.set('_codearena_source', event.data.source);
      pyodide.globals.set('_codearena_input', testCase.input_data || '');
      const rawResult = pyodide.runPython('_codearena_run(_codearena_source, _codearena_input)');
      results.push({
        name: testCase.name,
        expected: testCase.expected_output || '',
        ...JSON.parse(rawResult),
      });
    }
    self.postMessage({ type: 'results', results });
  } catch (error) {
    self.postMessage({ type: 'error', message: error.message || 'The code could not be run.' });
  }
});