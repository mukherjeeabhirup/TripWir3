/* Adapted from pingdotgg/t3code @ 20fcc6ca57195cf9180114387e4f659d8e1ee2b4.
 * Copyright (c) 2026 T3 Tools Inc. MIT; see /static/NOTICE.txt.
 * WorkLog.tsx: WorkLogLine/Row/Details ported from React/Tailwind to DOM/CSS.
 * ui/collapsible.tsx: root/trigger/panel slots with native details semantics.
 * TimelineWorkGroupRows.logic.ts: working timer, same invalid-date guard.
 */
"use strict";
const T3WorkLog = (() => {
  const LIVE_EDGE_PX = 4;
  function atLiveEdge(scroller) {
    return scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight <= LIVE_EDGE_PX;
  }
  function workingTimer(startIso, endIso) {
    const start = Date.parse(startIso), end = Date.parse(endIso);
    if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
    const seconds = Math.max(0, Math.floor((end - start)/1000));
    return seconds < 60 ? `${seconds}s` : `${Math.floor(seconds/60)}m ${seconds % 60}s`;
  }
  function row({icon, label, trailing, body}) {
    const details = document.createElement('details'); details.className = 'work-log-row'; details.dataset.slot = 'collapsible';
    const summary = document.createElement('summary'); summary.className = 'work-log-line'; summary.dataset.slot = 'collapsible-trigger';
    const glyph = document.createElement('span'); glyph.className = 'work-log-icon'; glyph.textContent = icon;
    const text = document.createElement('span'); text.className = 'work-log-label'; text.textContent = label; text.title = label;
    const tail = document.createElement('span'); tail.className = 'work-log-trailing'; tail.textContent = trailing;
    summary.append(glyph, text, tail); details.append(summary);
    body.classList.add('work-log-details'); body.dataset.slot = 'collapsible-panel'; details.append(body);
    // Native disclosure supplies keyboard semantics without Base UI/React.
    const sync = () => { details.dataset.state = details.open ? 'open' : 'closed'; };
    details.addEventListener('toggle', sync); sync();
    return details;
  }
  return {atLiveEdge, workingTimer, row};
})();
