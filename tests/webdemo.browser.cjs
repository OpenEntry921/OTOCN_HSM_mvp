const { chromium } = require("playwright");
const assert = require("node:assert/strict");
(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1050 },
  });
  let errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("http://127.0.0.1:8080");
  await page.waitForSelector("#trade");
  await page.route(
    /\/api\/runs\/[^/]+$/,
    async (route) => {
      const response = await route.fetch();
      const body = await response.json();
      body.result = null;
      body.events = [];
      await route.fulfill({ response, json: body });
    },
    { times: 1 },
  );
  for (const [scenario, expected, count] of [
    ["normal", "실행 성공", "1회"],
    ["amount_tamper", "차단", "0회"],
    ["address_tamper", "차단", "0회"],
    ["replay", "실행 성공", "1회"],
    ["expired", "차단", "0회"],
    ["unsigned", "차단", "0회"],
    ["untrusted", "차단", "0회"],
    ["relay_compromise", "차단", "0회"],
    ["policy", "차단", "0회"],
    ["cache", "실행 성공", "1회"],
  ]) {
    await page.selectOption("#scenario", scenario);
    await page.click("#execute");
    await page.waitForFunction(
      () =>
        document.querySelector("#connection").textContent.includes("결과") ||
        document.querySelector("#connection").textContent.includes("복구 완료"),
    );
    await page.waitForSelector(".receipt");
    assert(
      (await page.locator(".verdict").textContent()).includes(expected),
      scenario,
    );
    assert.equal(await page.locator(".count").textContent(), count);
    const id = await page.evaluate(() => localStorage.getItem("otocn-run"));
    const response = await page.request.get(
      "http://127.0.0.1:8080/api/runs/" + id,
    );
    const output = await response.json();
    assert.equal(
      await page.locator("#events tr").count(),
      output.events.length,
    );
    for (const [stage] of Object.entries({
      application: 1,
      approval: 1,
      relay: 1,
      ndn: 1,
      endpoint: 1,
      audit: 1,
    })) {
      const ev = output.events.filter((e) => e.stage === stage).at(-1);
      if (ev)
        assert.equal(
          await page.locator("#node-" + stage).getAttribute("data-state"),
          ev.status,
        );
    }
    console.log("UI PASS", scenario);
  }
  await page.locator("#node-ndn summary").click();
  await page.screenshot({ path: "/tmp/otocn-desktop.png", fullPage: true });
  await page.reload();
  await page.waitForSelector(".receipt");
  assert.equal(await page.locator(".count").textContent(), "1회");
  console.log("PASS refresh recovery");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "/tmp/otocn-mobile.png", fullPage: true });
  assert(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  );
  console.log("PASS mobile no horizontal overflow");

  await page.unroute("**/api/runs");
  await page.route("**/api/runs", (r) => r.abort());
  await page.click("#execute");
  await page.waitForFunction(() =>
    document.querySelector("#connection").textContent.includes("요청 오류"),
  );
  assert((await page.locator("#connection").textContent()).includes("오류"));
  assert.equal(await page.locator(".receipt").count(), 0);
  console.log("PASS failed request error without stale success");
  await page.unroute("**/api/runs");
  const created = await page.request.post("http://127.0.0.1:8080/api/runs", {
    data: {
      requester: "operator",
      asset: "DUSD",
      network: "demo-net",
      amount: "1.00",
      target: "wallet_A",
      scenario: "normal",
    },
  });
  const rid = (await created.json()).request_id;
  await page.route(
    /\/api\/runs\/[^/]+$/,
    async (route) => {
      const response = await route.fetch();
      const body = await response.json();
      body.result = null;
      body.events = [];
      await route.fulfill({ response, json: body });
    },
    { times: 1 },
  );
  await page.route("**/events?*", (r) => r.abort());
  await page.evaluate((id) => openRun(id), rid);
  await page.waitForFunction(() =>
    document.querySelector("#connection").textContent.includes("연결 오류"),
  );
  assert.equal(await page.locator(".receipt").count(), 0);
  console.log("PASS SSE failure without success");
  assert.deepEqual(errors, []);
  await browser.close();
})();
