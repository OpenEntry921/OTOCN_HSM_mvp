"use strict";
const $ = (s) => document.querySelector(s);
const labels = {
  application: "애플리케이션 서버",
  approval: "독립 승인 서비스",
  relay: "Relay 정책 게이트",
  ndn: "NDN 모의 전달",
  endpoint: "Endpoint / HSM",
  audit: "감사 기록",
};
const states = {
  waiting: "○ 대기",
  processing: "◌ 처리 중",
  passed: "✓ 통과",
  blocked: "⊘ 차단",
  error: "! 시스템 오류",
  success: "✓ 실행 성공",
};
const icons = {
  application:
    '<rect x="15" y="8" width="50" height="48" rx="4"/><path d="M15 24h50M15 40h50M23 16h4m-4 16h4m-4 16h4M50 16h8m-8 16h8m-8 16h8"/>',
  approval:
    '<rect x="20" y="12" width="42" height="45" rx="3"/><path d="M30 12V7h20v10H30M28 29l4 4 7-8m4 5h11M28 43l4 4 7-8m4 5h11"/>',
  relay:
    '<path d="M12 56V16h56v40M23 56V27h34v29M8 56h64M21 8h38"/><path d="M31 40l7 7 13-15"/>',
  ndn: '<circle cx="15" cy="16" r="7"/><circle cx="65" cy="16" r="7"/><circle cx="40" cy="49" r="8"/><circle cx="40" cy="23" r="5"/><path d="M22 16h36M19 22l16 21m26-21L45 43M40 28v13"/>',
  endpoint:
    '<rect x="12" y="7" width="56" height="50" rx="5"/><rect x="28" y="28" width="24" height="20" rx="3"/><path d="M32 28v-7a8 8 0 0116 0v7M40 36v6M18 14h8m28 36h8"/>',
  audit:
    '<path d="M18 8h39v48H18zM24 8v48M30 20h20m-20 10h20m-20 10h13M53 40l5 5 12-14"/>',
};
const flows = {
  application: "① 거래 요청",
  approval: "② 승인 증명 ↓",
  relay: "③ 실행 토큰 ↓",
  ndn: "④ Interest ⇄ Data",
  endpoint: "⑤ 독립 검증 → 모의 서명",
  audit: "⑥ 영속 이벤트 ↓",
};
let source = null,
  current = null,
  snapshot = null,
  seen = 0,
  playback = Promise.resolve(),
  generation = 0;
const pause = () => new Promise((resolve) => setTimeout(resolve, 75));
function reset() {
  $("#nodes").replaceChildren();
  $("#events").replaceChildren();
  seen = 0;
  snapshot = null;
  for (const [key, name] of Object.entries(labels)) {
    const el = document.createElement("details");
    el.className = "node";
    el.id = "node-" + key;
    el.dataset.state = "waiting";
    el.innerHTML = `<span class="flow"></span><summary><svg viewBox="0 0 80 65" aria-hidden="true">${icons[key]}</svg><strong></strong><span class="state"></span></summary><pre>아직 데이터가 없습니다.</pre>`;
    el.querySelector(".flow").textContent = flows[key];
    el.querySelector("strong").textContent = name;
    el.querySelector(".state").textContent = states.waiting;
    $("#nodes").append(el);
  }
}
function event(e) {
  if (e.seq <= seen) return;
  seen = e.seq;
  const node = $("#node-" + e.stage);
  if (node) {
    node.dataset.state = e.status;
    node.querySelector(".state").textContent =
      (states[e.status] || e.status) + " · " + e.reason;
    node.querySelector("pre").textContent =
      (node.querySelector("pre").textContent === "아직 데이터가 없습니다."
        ? ""
        : node.querySelector("pre").textContent + "\n\n") +
      "#" +
      e.seq +
      " " +
      e.reason +
      "\n" +
      JSON.stringify(e.details, null, 2);
  }
  const tr = document.createElement("tr");
  for (const value of [
    e.seq,
    new Date(e.timestamp * 1000).toLocaleTimeString("ko-KR", {
      timeZone: "Asia/Seoul",
    }),
    labels[e.actor] || e.actor,
    states[e.status] || e.status,
    e.reason,
  ]) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.append(td);
  }
  $("#events").append(tr);
}
function receipt(r) {
  const root = document.createElement("div");
  root.className = "receipt";
  root.dataset.status = r.status;
  const title = document.createElement("div");
  title.className = "verdict";
  title.textContent = states[r.status] || r.status;
  root.append(title);
  const count = document.createElement("div");
  count.className = "count";
  count.textContent = r.execution_count + "회";
  root.append(count);
  const dl = document.createElement("dl");
  for (const [k, v] of Object.entries({
    "요청 ID": r.request_id,
    "승인된 거래": r.approved_transaction
      ? `${r.approved_transaction.requester} · ${r.approved_transaction.amount} ${r.approved_transaction.asset} · ${r.approved_transaction.network} → ${r.approved_transaction.target}`
      : "승인 없음",
    "차단 단계": r.blocked_stage ? labels[r.blocked_stage] : "—",
    사유: r.reason,
    "모의 서명값 (실제 자산 서명 아님)": r.mock_signature || "—",
    "서버 처리 시간": r.duration_ms + " ms",
  })) {
    const dt = document.createElement("dt"),
      dd = document.createElement("dd");
    dt.textContent = k;
    dd.textContent = v;
    dl.append(dt, dd);
  }
  root.append(dl);
  $("#result").replaceChildren(root);
}
async function json(url, options) {
  const r = await fetch(url, options);
  if (!r.ok) {
    let msg = "HTTP " + r.status;
    try {
      msg += " · " + (await r.json()).detail;
    } catch {}
    throw new Error(msg);
  }
  return r.json();
}
async function history() {
  const runs = await json("/api/runs");
  const sel = $("#history");
  sel.replaceChildren(new Option("실행 기록 선택", ""));
  for (const r of runs) {
    const result = r.result ? JSON.parse(r.result) : null;
    sel.add(
      new Option(
        new Date(r.created * 1000).toLocaleString("ko-KR", {
          timeZone: "Asia/Seoul",
        }) +
          " · " +
          (result ? states[result.status] : "처리 중") +
          " · " +
          r.id.slice(0, 8),
        r.id,
      ),
    );
  }
  if (current) sel.value = current;
}
async function openRun(id) {
  const turn = ++generation;
  if (source) source.close();
  reset();
  playback = Promise.resolve();
  current = id;
  localStorage.setItem("otocn-run", id);
  $("#connection").textContent = "서버 이벤트 연결 중…";
  $("#download").hidden = false;
  $("#download").href = "/api/runs/" + encodeURIComponent(id) + "/download";
  $("#result").textContent = "처리 중 · 아직 성공이 확인되지 않았습니다.";
  try {
    snapshot = await json("/api/runs/" + encodeURIComponent(id));
    for (const e of snapshot.events) {
      if (turn !== generation) return;
      event(e);
      await pause();
    }
    if (snapshot.result) {
      receipt(snapshot.result);
      $("#connection").textContent = "저장된 결과 복구 완료";
      $("#raw").textContent = JSON.stringify(snapshot, null, 2);
      return;
    }
    source = new EventSource(
      "/api/runs/" + encodeURIComponent(id) + "/events?after=" + seen,
    );
    source.addEventListener("stage", (e) => {
      playback = playback.then(async () => {
        if (turn !== generation) return;
        event(JSON.parse(e.data));
        await pause();
      });
      $("#connection").textContent = "실제 백엔드 이벤트 수신 중";
    });
    source.addEventListener("complete", async (e) => {
      await playback;
      if (turn !== generation) return;
      receipt(JSON.parse(e.data));
      source.close();
      $("#connection").textContent = "실행 결과 수신 완료";
      try {
        snapshot = await json("/api/runs/" + encodeURIComponent(id));
        $("#raw").textContent = JSON.stringify(snapshot, null, 2);
        await history();
      } catch (err) {
        $("#connection").textContent =
          "결과 수신 후 기록 조회 오류: " + err.message;
      }
    });
    source.onerror = () => {
      $("#connection").textContent =
        "연결 오류 · 재연결 중. 성공을 확인할 수 없습니다.";
    };
  } catch (err) {
    $("#connection").textContent = "조회 오류: " + err.message;
    $("#result").textContent = "시스템 연결 오류 · 실행 성공 여부 확인 불가";
  }
}
$("#trade").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("#execute").disabled = true;
  ++generation;
  if (source) source.close();
  reset();
  $("#result").textContent = "요청 전송 중 · 성공 여부 확인 전";
  $("#download").hidden = true;
  $("#connection").textContent = "요청 전송 중…";
  try {
    const data = Object.fromEntries(new FormData(e.target));
    const r = await json("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    await openRun(r.request_id);
    await history();
  } catch (err) {
    $("#connection").textContent = "요청 오류: " + err.message;
  } finally {
    $("#execute").disabled = false;
  }
});
$("#scenario").onchange = () => {
  $("#attack").textContent =
    $("#scenario").value === "relay_compromise"
      ? "Relay 키 탈취·요청 변조 가정, 독립 승인 서비스와 Endpoint는 정상"
      : "공격 시나리오는 실제 검증 입력을 변경합니다.";
};
$("#history").onchange = (e) => {
  if (e.target.value) openRun(e.target.value);
};
$("#refresh").onclick = () =>
  history().catch((e) => ($("#connection").textContent = e.message));
$("#json").onclick = () => {
  $("#raw").hidden = !$("#raw").hidden;
  $("#raw").textContent = snapshot
    ? JSON.stringify(snapshot, null, 2)
    : "실행 기록을 선택하세요.";
};
reset();
history().catch(
  (e) => ($("#connection").textContent = "이력 조회 오류: " + e.message),
);
const saved = localStorage.getItem("otocn-run");
if (saved) openRun(saved);
