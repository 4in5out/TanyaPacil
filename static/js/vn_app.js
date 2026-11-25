(() => {
  const customAssets = window.TANYAPACIL_ASSETS || {};
  const audio = new window.PakChillAudio(customAssets);

  // DOM elements
  const mascotWrapper = document.getElementById('mascotWrapper');
  const mascotCustomImg = document.getElementById('mascotCustomImg');
  const statePill = document.getElementById('vnStatePill');
  const stateLabel = document.getElementById('vnStateLabel');
  const dialogueScroll = document.getElementById('vnDialogueScroll');
  const dialogueContent = document.getElementById('vnDialogueContent');
  const userEcho = document.getElementById('vnUserEcho');
  const citationsEl = document.getElementById('vnCitations');
  const starterChips = document.getElementById('starterChips');

  const chatForm = document.getElementById('vnChatForm');
  const chatInput = document.getElementById('vnChatInput');
  const sendBtn = document.getElementById('vnSendBtn');
  const skipBtn = document.getElementById('vnSkipBtn');

  const bgmBtn = document.getElementById('btnToggleBgm');
  const sfxBtn = document.getElementById('btnToggleSfx');
  const backlogBtn = document.getElementById('btnOpenBacklog');
  const resourcesBtn = document.getElementById('btnOpenResources');
  const resetBtn = document.getElementById('btnResetChat');

  const backlogModal = document.getElementById('backlogModal');
  const backlogBody = document.getElementById('backlogBody');
  const resourcesModal = document.getElementById('resourcesModal');
  const resourcesBody = document.getElementById('resourcesBody');

  let typingTimer = null;
  let fullReplyMarkdown = '';
  let currentCitations = [];
  let isSending = false;

  // ===== CSRF HELPER =====
  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split('; ') : [];
    for (const c of cookies) {
      const [k, ...v] = c.split('=');
      if (k === name) return decodeURIComponent(v.join('='));
    }
    return '';
  }

  // ===== MASCOT 3-STATE CONTROLLER =====
  const STATE_LABELS = {
    idle: 'Chilling',
    thinking: 'Thinking...',
    answering: 'Explaining',
  };

  function setMascotState(state) {
    const valid = ['idle', 'thinking', 'answering'].includes(state) ? state : 'idle';
    mascotWrapper.dataset.state = valid;
    statePill.dataset.state = valid;
    stateLabel.textContent = STATE_LABELS[valid];

    if (mascotCustomImg) {
      const customMap = {
        idle: customAssets.mascot_idle,
        thinking: customAssets.mascot_thinking || customAssets.mascot_idle,
        answering: customAssets.mascot_answering || customAssets.mascot_idle,
      };
      if (customMap[valid]) {
        mascotCustomImg.src = customMap[valid];
      }
    }
  }

  // ===== SAFE LIGHTWEIGHT MARKDOWN RENDERER =====
  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatInline(text) {
    return text
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*]+)\*/g, '<em>$1</em>');
  }

  function renderMarkdown(md) {
    const codeBlocks = [];
    let working = (md || '').replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
      const idx = codeBlocks.length;
      const safeLang = escapeHtml(lang || 'python');
      const safeCode = escapeHtml(code.replace(/\n$/, ''));
      codeBlocks.push(
        `<div class="code-block-wrap">` +
          `<div class="code-block-header"><span>${safeLang}</span>` +
          `<button type="button" class="copy-code-btn" data-copy-idx="${idx}">Copy</button></div>` +
          `<pre><code>${safeCode}</code></pre></div>`
      );
      return `@@CODEBLOCK_${idx}@@`;
    });

    const lines = escapeHtml(working).split('\n');
    let html = '';
    let inList = false;

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        continue;
      }
      if (/^@@CODEBLOCK_\d+@@$/.test(trimmed)) {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        html += trimmed;
        continue;
      }
      if (/^[-*]\s+/.test(trimmed)) {
        if (!inList) {
          html += '<ul>';
          inList = true;
        }
        html += `<li>${formatInline(trimmed.replace(/^[-*]\s+/, ''))}</li>`;
        continue;
      }
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<p>${formatInline(trimmed)}</p>`;
    }
    if (inList) html += '</ul>';

    codeBlocks.forEach((block, idx) => {
      html = html.replace(`@@CODEBLOCK_${idx}@@`, block);
    });
    return html;
  }

  function attachCopyButtons(container) {
    container.querySelectorAll('.copy-code-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const codeEl = btn.closest('.code-block-wrap')?.querySelector('code');
        if (!codeEl) return;
        navigator.clipboard?.writeText(codeEl.textContent || '').then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => { btn.textContent = 'Copy'; }, 1400);
        });
      });
    });
  }

  function renderCitations(citations) {
    citationsEl.innerHTML = '';
    if (!citations || !citations.length) return;
    citations.forEach((c) => {
      const icon = c.resource_type === 'PDF' ? '📄' : c.resource_type === 'EXTERNAL' ? '🌐' : '📝';
      const href = c.source_url || c.file_url || '';
      if (href) {
        const a = document.createElement('a');
        a.className = 'citation-chip';
        a.href = href;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.textContent = `${icon} ${c.title}`;
        citationsEl.appendChild(a);
      } else {
        const span = document.createElement('span');
        span.className = 'citation-chip';
        span.textContent = `${icon} ${c.title}`;
        citationsEl.appendChild(span);
      }
    });
  }

  // ===== TYPEWRITER + UNDERTALE VOICE BLIP =====
  function finishTypingImmediately() {
    if (typingTimer) {
      clearTimeout(typingTimer);
      typingTimer = null;
    }
    dialogueContent.innerHTML = renderMarkdown(fullReplyMarkdown);
    attachCopyButtons(dialogueContent);
    renderCitations(currentCitations);
    skipBtn.classList.remove('visible');
    setMascotState('idle');
    dialogueScroll.scrollTop = dialogueScroll.scrollHeight;
  }

  function typewriteResponse(markdownText, citations = []) {
    if (typingTimer) clearTimeout(typingTimer);
    fullReplyMarkdown = markdownText || '';
    currentCitations = citations;
    citationsEl.innerHTML = '';
    setMascotState('answering');
    skipBtn.classList.add('visible');

    let index = 0;
    const total = fullReplyMarkdown.length;
    const stepSize = total > 600 ? 4 : total > 300 ? 3 : 2;
    let insideCodeFence = false;

    function tick() {
      index = Math.min(index + stepSize, total);
      const slice = fullReplyMarkdown.slice(0, index);

      // Detect if currently typing inside ``` code block (mute voice blips during code)
      const fenceCount = (slice.match(/```/g) || []).length;
      insideCodeFence = fenceCount % 2 === 1;

      const lastChar = fullReplyMarkdown[index - 1] || '';
      if (!insideCodeFence) {
        audio.playVoiceBlip(lastChar);
      }

      // Render raw escaped preview while typing, full Markdown when finished
      dialogueContent.innerHTML = renderMarkdown(slice);
      dialogueScroll.scrollTop = dialogueScroll.scrollHeight;

      if (index < total) {
        const delay = insideCodeFence ? 8 : 24;
        typingTimer = setTimeout(tick, delay);
      } else {
        finishTypingImmediately();
      }
    }

    tick();
  }

  // ===== CHAT SUBMISSION =====
  async function sendQuestion(questionText) {
    const message = (questionText || '').trim();
    if (!message || isSending) return;

    if (typingTimer) {
      clearTimeout(typingTimer);
      typingTimer = null;
    }

    isSending = true;
    sendBtn.disabled = true;
    chatInput.value = '';
    if (starterChips) starterChips.style.display = 'none';

    userEcho.textContent = `You asked: "${message}"`;
    userEcho.classList.add('visible');
    citationsEl.innerHTML = '';

    setMascotState('thinking');
    dialogueContent.innerHTML = '<p><em>Hmm... bentar ya, Pak Chill cek catatan modul dulu...</em></p>';

    try {
      const resp = await fetch('/api/chat/send/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ message }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        typewriteResponse(data.error || 'Oops, something went wrong on the server.');
      } else {
        typewriteResponse(data.reply, data.citations || []);
      }
    } catch (err) {
      typewriteResponse('Waduh, koneksi ke server lagi terputus. Coba kirim lagi ya!');
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendQuestion(chatInput.value);
  });

  skipBtn.addEventListener('click', () => finishTypingImmediately());
  dialogueScroll.addEventListener('click', () => {
    if (typingTimer) finishTypingImmediately();
  });

  document.querySelectorAll('.starter-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      sendQuestion(chip.dataset.prompt || chip.textContent);
    });
  });

  // ===== AUDIO HUD CONTROLS =====
  bgmBtn.addEventListener('click', () => {
    const on = audio.toggleBgm();
    bgmBtn.classList.toggle('active', on);
    bgmBtn.querySelector('.btn-label').textContent = on ? 'BGM: On' : 'BGM: Off';
  });

  sfxBtn.addEventListener('click', () => {
    const on = audio.toggleSfx();
    sfxBtn.classList.toggle('active', on);
    sfxBtn.querySelector('.btn-label').textContent = on ? 'Voice: On' : 'Voice: Off';
  });

  // ===== BACKLOG MODAL =====
  async function openBacklog() {
    backlogModal.classList.add('open');
    backlogBody.innerHTML = '<p style="color: var(--vn-muted);">Loading classroom backlog...</p>';
    try {
      const resp = await fetch('/api/chat/history/');
      const data = await resp.json();
      if (!data.messages || !data.messages.length) {
        backlogBody.innerHTML = '<p style="color: var(--vn-muted);">No messages yet. Ask Pak Chill your first question!</p>';
        return;
      }
      backlogBody.innerHTML = data.messages
        .map((m) => {
          const who = m.sender === 'user' ? '🧑‍🎓 You' : '🐼 Pak Chill';
          return (
            `<div class="backlog-item ${m.sender}">` +
              `<div class="backlog-meta"><strong>${who}</strong><span>${escapeHtml(m.created_at)}</span></div>` +
              `<div class="backlog-content">${renderMarkdown(m.content)}</div>` +
            `</div>`
          );
        })
        .join('');
      attachCopyButtons(backlogBody);
    } catch {
      backlogBody.innerHTML = '<p style="color: var(--vn-muted);">Failed to load backlog.</p>';
    }
  }

  // ===== RESOURCES MODAL =====
  async function openResources() {
    resourcesModal.classList.add('open');
    resourcesBody.innerHTML = '<p style="color: var(--vn-muted);">Loading faculty coding resources...</p>';
    try {
      const resp = await fetch('/api/resources/');
      const data = await resp.json();
      if (!data.resources || !data.resources.length) {
        resourcesBody.innerHTML =
          '<p style="color: var(--vn-muted);">No resources uploaded yet. Add PDFs or GFG/W3Schools links in <a href="/admin/" target="_blank" style="color: var(--vn-accent);">Django Admin</a>!</p>';
        return;
      }
      resourcesBody.innerHTML = data.resources
        .map((r) => {
          const badge = r.resource_type === 'PDF' ? '📄 PDF' : r.resource_type === 'EXTERNAL' ? '🌐 Web' : '📝 Note';
          const openLink = r.source_url || r.file_url;
          const linkBtn = openLink
            ? `<a class="mini-btn" href="${escapeHtml(openLink)}" target="_blank" rel="noopener">Open</a>`
            : '';
          return (
            `<div class="resource-card">` +
              `<div>` +
                `<div class="resource-title">${escapeHtml(r.category_icon)} ${escapeHtml(r.title)} <span style="font-size:0.74rem;color:var(--vn-accent-2);font-weight:500;">(${badge})</span></div>` +
                `<div class="resource-summary">${escapeHtml(r.summary || 'Indexed faculty study material.')}</div>` +
              `</div>` +
              `<div class="resource-actions">` +
                `${linkBtn}` +
                `<button type="button" class="mini-btn ask-resource-btn" data-title="${escapeHtml(r.title)}">Ask Pak Chill</button>` +
              `</div>` +
            `</div>`
          );
        })
        .join('');

      resourcesBody.querySelectorAll('.ask-resource-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
          resourcesModal.classList.remove('open');
          sendQuestion(`Jelasin materi dari "${btn.dataset.title}" secara singkat dan jelas dong, Pak Chill!`);
        });
      });
    } catch {
      resourcesBody.innerHTML = '<p style="color: var(--vn-muted);">Failed to load resources.</p>';
    }
  }

  backlogBtn.addEventListener('click', openBacklog);
  resourcesBtn.addEventListener('click', openResources);

  document.querySelectorAll('[data-close-modal]').forEach((btn) => {
    btn.addEventListener('click', () => {
      backlogModal.classList.remove('open');
      resourcesModal.classList.remove('open');
    });
  });

  [backlogModal, resourcesModal].forEach((backdrop) => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) backdrop.classList.remove('open');
    });
  });

  // ===== RESET SESSION =====
  resetBtn.addEventListener('click', async () => {
    if (typingTimer) clearTimeout(typingTimer);
    await fetch('/api/chat/reset/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
    });
    userEcho.classList.remove('visible');
    citationsEl.innerHTML = '';
    if (starterChips) starterChips.style.display = 'flex';
    typewriteResponse(
      "Fresh board, fresh mind! 🐼✨ Mau bahas materi DDP1, Python, atau resource modul yang mana sekarang?"
    );
  });

  // ===== INITIAL GREETING =====
  setMascotState('idle');
  dialogueContent.innerHTML = renderMarkdown(
    "Halo! Aku **Pak Chill** — panda mentor santai di kelas **TanyaPacil**. 🐼☕\n\n" +
    "Lagi bingung sama materi **DDP1**, slide PDF kuliah, atau referensi Python dari **GFG / W3Schools**? " +
    "Santai aja, tanyakan di bawah ya — kita bedah pelan-pelan sampai paham!"
  );
})();
