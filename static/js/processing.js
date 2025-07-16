// processing.js

document.addEventListener('DOMContentLoaded', () => {
  const startBtn = document.getElementById('start-btn');
  const cancelBtn = document.getElementById('cancel-btn');
  const form = document.getElementById('plugins-form');
  const logDiv = document.getElementById('log');
  let evtSource;
  let currentTaskId;

  startBtn.addEventListener('click', () => {
    const formData = new FormData(form);
    fetch(window.location.pathname + '/start', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      currentTaskId = data.task_id;
      evtSource = new EventSource(window.location.pathname + '/events');
      evtSource.onmessage = e => {
        const p = document.createElement('p');
        p.textContent = e.data;
        logDiv.appendChild(p);
        logDiv.scrollTop = logDiv.scrollHeight;
      };
    });
  });

  cancelBtn.addEventListener('click', () => {
    if (confirm('Cancel this project?')) {
      fetch(window.location.pathname + '/cancel?task_id=' + currentTaskId, {
        method: 'DELETE'
      }).then(() => {
        if (evtSource) evtSource.close();
        logDiv.innerHTML += '<p>Analysis cancelled.</p>';
      });
    }
  });
});
// when the page loads, open an EventSource to the events endpoint
window.addEventListener('DOMContentLoaded', () => {
  const output = document.getElementById('log-output');
  const es = new EventSource(`/processing/${projectId}/events`);
  es.onmessage = e => {
    output.innerText += e.data + '\n';
    output.scrollTop = output.scrollHeight;
  };
  es.onerror = () => {
    es.close();
    output.innerText += '\n⏹️ Stream closed.';
  };
});
