/**
 * Tests for job-executor: scheduling loop, execution, rescheduling.
 */
import { describe, it, before, after, beforeEach } from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs/promises";
import * as path from "node:path";
import * as os from "node:os";
import {
  loadJobStore,
  saveJobStore,
  invalidateJobStoreCache,
  overrideConfigDir,
  resetConfigDir,
  buildJob,
  patchJobState,
} from "../job-store.js";
import { JobExecutor } from "../job-executor.js";
import type { CronJob } from "../types.js";

describe("job-executor", () => {
  let tmpDir: string;

  before(async () => {
    tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "trimc-executor-"));
    overrideConfigDir(tmpDir);
  });

  after(async () => {
    resetConfigDir();
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  beforeEach(() => {
    invalidateJobStoreCache();
  });

  // ── lifecycle ──────────────────────────────────────────────────

  it("starts and stops cleanly", () => {
    const executor = new JobExecutor(async () => {});
    assert.equal(executor.isRunning, false);
    executor.start();
    assert.equal(executor.isRunning, true);
    executor.stop();
    assert.equal(executor.isRunning, false);
  });

  it("double-start is a no-op", () => {
    const executor = new JobExecutor(async () => {});
    executor.start();
    executor.start();
    assert.equal(executor.isRunning, true);
    executor.stop();
  });

  // ── job execution ──────────────────────────────────────────────

  it("executes due jobs", async () => {
    const executedIds: string[] = [];
    const executor = new JobExecutor(async (job) => {
      executedIds.push(job.id);
    });

    // Create a job due "now" (every schedule with small interval)
    const job = buildJob({
      name: "fire-immediately",
      enabled: true,
      schedule: { kind: "every", everyMs: 100 }, // fires every 100ms
      payload: {},
    });
    // Force nextRunAtMs to be in the past
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job });

    executor.start();

    // Wait for execution
    await new Promise((r) => setTimeout(r, 500));

    executor.stop();

    assert.ok(
      executedIds.includes(job.id),
      `Expected job ${job.id} to execute, got: ${executedIds.join(", ")}`,
    );
  });

  it("respects enabled: false", async () => {
    const executedIds: string[] = [];
    const executor = new JobExecutor(async (job) => {
      executedIds.push(job.id);
    });

    const job = buildJob({
      name: "disabled-job",
      enabled: false,
      schedule: { kind: "every", everyMs: 100 },
      payload: {},
    });
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 300));
    executor.stop();

    assert.equal(executedIds.includes(job.id), false);
  });

  // ── state update after execution ───────────────────────────────

  it("updates runCount and lastRunStatus after execution", async () => {
    const executor = new JobExecutor(async () => {
      // successful execution
    });

    const job = buildJob({
      name: "state-check",
      enabled: true,
      schedule: { kind: "every", everyMs: 100 },
      payload: {},
    });
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 500));
    executor.stop();

    // Re-read from store
    invalidateJobStoreCache();
    const loaded = await loadJobStore();
    const updated = loaded[job.id];
    assert.ok(updated, "job should still exist");
    assert.ok(updated!.state.runCount >= 1, `runCount=${updated.state.runCount}`);
    assert.equal(updated.state.lastRunStatus, "ok");
    assert.equal(updated.state.runningAtMs, null, "should not be stuck running");
    assert.ok(
      typeof updated.state.lastDurationMs === "number" &&
        updated.state.lastDurationMs !== null,
    );
  });

  it("records error status on handler failure", async () => {
    const executor = new JobExecutor(async () => {
      throw new Error("boom");
    });

    const job = buildJob({
      name: "error-job",
      enabled: true,
      schedule: { kind: "every", everyMs: 100 },
      payload: {},
    });
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 500));
    executor.stop();

    invalidateJobStoreCache();
    const loaded = await loadJobStore();
    const updated = loaded[job.id];
    assert.ok(updated, "job should still exist");
    assert.equal(updated!.state.lastRunStatus, "error");
    assert.ok(updated!.state.lastError?.includes("boom"));
    assert.ok(updated!.state.consecutiveErrors >= 1);
  });

  // ── rescheduling ───────────────────────────────────────────────

  it("computes nextRunAtMs after execution", async () => {
    const executor = new JobExecutor(async () => {});

    const job = buildJob({
      name: "reschedule-test",
      enabled: true,
      schedule: { kind: "every", everyMs: 3600_000 }, // 1 hour
      payload: {},
    });
    const originalNext = job.state.nextRunAtMs;
    job.state.nextRunAtMs = Date.now() - 1; // force immediate

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 500));
    executor.stop();

    invalidateJobStoreCache();
    const loaded = await loadJobStore();
    const updated = loaded[job.id];
    assert.ok(updated, "job should still exist");
    assert.ok(updated!.state.nextRunAtMs !== null);
    assert.ok(updated!.state.nextRunAtMs! > Date.now(), "next run should be in the future");
  });

  // ── sgB fix G1 · 族1: stale-running guard (anchor 1) ──────────

  it("stale guard: clears a stale running mark and lets the job fire again", async () => {
    const executedIds: string[] = [];
    const executor = new JobExecutor(
      async (job) => {
        executedIds.push(job.id);
      },
      { staleRunningMs: 100 },
    );

    const job = buildJob({
      name: "stale-orphan",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      payload: {},
    });
    job.state.runningAtMs = Date.now() - 1_000; // stuck 1s > 100ms threshold → orphaned
    job.state.nextRunAtMs = Date.now() - 1; // due now

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 400));
    executor.stop();

    invalidateJobStoreCache();
    const loaded = await loadJobStore();
    const updated = loaded[job.id];
    assert.ok(updated, "job should still exist");
    assert.equal(updated!.state.runningAtMs, null, "stale mark must be cleared (persisted)");
    assert.ok(
      executedIds.includes(job.id),
      `job should fire after stale clear, got: ${executedIds.join(", ")}`,
    );
  });

  it("stale guard: does not touch a fresh running mark", async () => {
    const executedIds: string[] = [];
    const executor = new JobExecutor(
      async (job) => {
        executedIds.push(job.id);
      },
      { staleRunningMs: 5_000 },
    );

    const job = buildJob({
      name: "fresh-running",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      payload: {},
    });
    job.state.runningAtMs = Date.now() - 50; // 50ms < 5s threshold → genuinely running
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 300));
    executor.stop();

    assert.equal(executedIds.includes(job.id), false, "fresh-running job must not fire");
    invalidateJobStoreCache();
    const loaded = await loadJobStore();
    const updated = loaded[job.id];
    assert.ok(updated, "job should still exist");
    assert.ok(updated!.state.runningAtMs !== null, "running mark must be preserved");
  });

  // ── sgB fix G1 · 族2: settle-failure containment (anchor 2) ───

  it("settle containment: keeps the scheduler alive when settle persist throws", async () => {
    const calls: string[] = [];
    const executor = new JobExecutor(
      async (job) => {
        calls.push(job.id);
      },
      { tickMs: 50 },
    );

    const job = buildJob({
      name: "settle-boom",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      payload: {},
    });
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job }); // warms memCache + writes jobs.json

    // Sabotage the persist target: jobs.json becomes a DIRECTORY.
    // settle reaches saveJobStore with a warm cache (loadJobStore short-circuits),
    // then copyFile(jobs.json → .bak) throws → settleJob rejects → must be
    // contained inside executeJob (warn + local clear), never killing the loop.
    const storePath = path.join(tmpDir, "cron", "jobs.json");
    await fs.rm(storePath);
    await fs.mkdir(storePath);

    executor.start();
    await new Promise((r) => setTimeout(r, 300));
    assert.ok(executor.isRunning, "scheduler loop must stay alive after settle failure");
    assert.ok(calls.includes(job.id), "handler should have run");

    // Repair the store → loop still ticks and fires again.
    await fs.rmdir(storePath);
    invalidateJobStoreCache();
    const repaired = patchJobState(job, {
      runningAtMs: null,
      nextRunAtMs: Date.now() - 1,
    });
    await saveJobStore({ [job.id]: repaired });
    executor.tick();
    await new Promise((r) => setTimeout(r, 300));
    executor.stop();

    assert.ok(
      calls.filter((id) => id === job.id).length >= 2,
      `job should fire again after repair, calls=${calls.length}`,
    );
  });

  it("settle containment: keeps the scheduler alive when settle finds the job missing (silent abandon)", async () => {
    const calls: string[] = [];
    const executor = new JobExecutor(
      async (job) => {
        calls.push(job.id);
        if (calls.length === 1) {
          // Simulate the job vanishing mid-run: settle's re-read finds no job
          // and abandons silently — the loop must survive regardless.
          await fs.rm(path.join(tmpDir, "cron", "jobs.json"));
          invalidateJobStoreCache();
        }
      },
      { tickMs: 50 },
    );

    const job = buildJob({
      name: "settle-vanish",
      enabled: true,
      schedule: { kind: "every", everyMs: 60_000 },
      payload: {},
    });
    job.state.nextRunAtMs = Date.now() - 1;

    await saveJobStore({ [job.id]: job });

    executor.start();
    await new Promise((r) => setTimeout(r, 300));
    assert.ok(executor.isRunning, "scheduler loop must stay alive after silent-abandon settle");

    // Restore the store → loop still ticks and fires again.
    invalidateJobStoreCache();
    const restored = patchJobState(job, {
      runningAtMs: null,
      nextRunAtMs: Date.now() - 1,
    });
    await saveJobStore({ [job.id]: restored });
    executor.tick();
    await new Promise((r) => setTimeout(r, 300));
    executor.stop();

    assert.ok(
      calls.filter((id) => id === job.id).length >= 2,
      `job should fire again after restore, calls=${calls.length}`,
    );
  });
});
