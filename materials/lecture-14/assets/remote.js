(() => {
  const remoteMode = new URL(location.href).searchParams.has('remote');
  const endpoint = 'https://course-slide-remote.den-rad.workers.dev';
  const send = (ws, data) => { if (ws?.readyState === WebSocket.OPEN) ws.send(JSON.stringify(data)); };
  let socket, active = true, reconnectTimer;
  const status = document.createElement('p');
  const panel = document.createElement('div');
  panel.className = 'remote-panel';
  const connect = (room, role) => {
    const wsUrl = new URL(`/room/${room}/socket?role=${role}`, endpoint); wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(wsUrl);
    socket.onopen = () => { status.textContent = role === 'remote' ? 'Соединение с сервером установлено' : 'Ожидаем телефон'; if (role === 'remote') send(socket, {type:'sync'}); else send(socket,{type:'state',current:current+1,total:slides.length}); };
    socket.onmessage = event => { let message; try { message = JSON.parse(event.data); } catch { return; }
      if (message.type === 'presence') { status.textContent = role === 'remote' ? (message.presenter ? 'Презентация подключена' : 'Ожидаем презентацию') : (message.remote ? 'Телефон подключён' : 'Ожидаем телефон'); if (role === 'presenter' && message.remote) send(socket,{type:'state',current:current+1,total:slides.length}); }
      if (role === 'remote' && message.type === 'state') document.querySelector('.remote-count').textContent = `${message.current} / ${message.total}`;
      if (role === 'presenter' && message.type === 'next') show(current+1);
      if (role === 'presenter' && message.type === 'previous') show(current-1);
      if (role === 'presenter' && message.type === 'sync') send(socket,{type:'state',current:current+1,total:slides.length});
    };
    socket.onclose = () => { status.textContent = 'Нет связи. Переподключаемся…'; if (active) reconnectTimer = setTimeout(() => connect(room, role), 2000); };
    socket.onerror = () => socket.close();
  };
  if (remoteMode) {
    const room = location.hash.slice(1);
    document.body.classList.add('remote-mode');
    panel.innerHTML = '<h1>Пульт презентации</h1><p class="remote-count">— / —</p><div class="remote-buttons"><button type="button" data-action="previous">← Назад</button><button type="button" data-action="next">Далее →</button></div>';
    panel.append(status); document.body.append(panel);
    panel.querySelectorAll('button').forEach(button => button.addEventListener('click', () => send(socket,{type:button.dataset.action})));
    if (/^[a-f0-9]{64}$/.test(room)) connect(room,'remote'); else status.textContent = 'Ссылка на комнату недействительна';
    return;
  }
  const button = document.createElement('button'); button.setAttribute('aria-label', 'Подключить телефон'); button.title = 'Подключить телефон'; button.innerHTML = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M10 18h4M9 6h6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'; button.className = 'remote-toggle'; document.body.append(button);
  panel.hidden = true; panel.innerHTML = '<h2>Подключить телефон</h2><div class="remote-qr"></div><button type="button" class="remote-stop">Закрыть сессию</button>';
  panel.append(status); document.body.append(panel);
  button.addEventListener('click', async () => {
    if (!panel.hidden) return;
    panel.hidden = false;
    if (location.protocol === 'file:') { status.textContent = 'Откройте презентацию через веб-сервер: file:// не поддерживается.'; return; }
    status.textContent = 'Создаём комнату…';
    try {
      const res = await fetch(`${endpoint}/room`, {method:'POST'}); if (!res.ok) throw new Error('room');
      const {room} = await res.json();
      const link = new URL(location.href); link.search = '?remote=1'; link.hash = room;
      const qr = qrcode(0,'M'); qr.addData(link.href); qr.make(); panel.querySelector('.remote-qr').innerHTML = qr.createSvgTag({cellSize:5,margin:8});
      active = true; connect(room,'presenter');
    } catch { status.textContent = 'Не удалось подключиться к сервису'; }
  });
  panel.querySelector('.remote-stop').addEventListener('click', () => { active=false; clearTimeout(reconnectTimer); send(socket,{type:'end'}); setTimeout(() => socket?.close(), 150); panel.hidden=true; });
  window.addEventListener('hashchange', () => send(socket,{type:'state',current:current+1,total:slides.length}));
})();
