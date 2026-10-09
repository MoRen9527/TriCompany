/**
 * Job Executor — scheduler loop that finds due jobs and executes them.
 *
 * Much simpler than openclaw's cron/service/timer.ts:
 *   - No heartbeat-wake coordination
 *   - No channel delivery / multi-target
 *   - No isolated-agent execution
 *   - No session reaper
 *   - No startup catchup (MVP scope)
 *
 * Approach: find next-due → setTimeout → execute → repeat.
 */

import { computeNextRunAtMs } from "./cron-engine.js";
import { resolveJobStaggerMs } from "./stagger.js";
import { loadJobStore, patchJobState, saveJobStore } from "./job-store.js";
import type { CronJob } from "./types.js";

/** Callback invoked when a job fires. Return value is ignored; throw to signal error. */
export type JobHandler = (job: CronJob) => Promise<void> | void;

export interface JobExecutorOptions {
  /** Minimum interval between scheduler ticks (ms). Default 1_000. */
  tickMs?: number;
  /** Maximum timer delay (ms). Default 60_000. */
  maxTimerDelayMs?: number;
  /**
   * Stale-running threshold (ms). A job whose runningAtMs has been set for
   * longer than this is treated as orphaned (daemon crashed/restarted
   * mid-run) and gets cleared so the job can fire again instead of being
   * skipped forever. Default 20min (= 2 × the consumer-side default job
   * timeout of 10min, mirroring the ×2 slack in the sgB fix plan).
   */
  staleRunningMs?: number;
}

const DEFAULT_TICK_MS = 1_000;
const DEFAULT_MAX_TIMER_DELAY_MS = 60_000;
const DEFAULT_STALE_RUNNING_MS = 20 * 60 * 1000;

export class JobExecutor {
  private handler: JobHandler;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private running = false;
  private tickMs: number;
  private maxTimerDelayMs: number;
  private staleRunningMs: number;

  constructor(handler: JobHandler, options: JobExecutorOptions = {}) {
    this.handler = handler;
    this.tickMs = options.tickMs ?? DEFAULT_TICK_MS;
    this.maxTimerDelayMs = options.maxTimerDelayMs ?? DEFAULT_MAX_TIMER_DELAY_MS;
    this.staleRunningMs = options.staleRunningMs ?? DEFAULT_STALE_RUNNING_MS;
  }

  // ── lifecycle ──────────────────────────────────────────────────

  /**
   * Start the executor loop. Safe to call multiple times (no-op if already running).
   */
  start(): void {
    if (this.running) return;
    this.running = true;
    this.scheduleNext();
  }

  /**
   * Stop the executor loop. Safe to call multiple times.
   */
  stop(): void {
    this.running = false;
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  get isRunning(): boolean {
    return this.running;
  }

  /**
   * Force an immediate tick — re-evaluates due jobs and reschedules.
   * Useful after adding/removing jobs externally.
   */
  tick(): void {
    if (this.timer !== null) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    this.scheduleNext();
  }

  // ── internal ───────────────────────────────────────────────────

  private async scheduleNext(): Promise<void> {
    if (!this.running) return;

    // Find all enabled jobs that are due
    const now = Date.now();
    const jobs = await loadJobStore();
    const dueJobs: CronJob[] = [];

    let soonestNextMs: number | null = null;

    for (const jobOriginal of Object.values(jobs)) {
      let job = jobOriginal; // rebindable: stale guard may swap in the cleared copy
      if (!job.enabled) continue;

      // Stale-running guard (sgB fix anchor 1): a "running" mark older than
      // the threshold is an orphan left by a crash/restart mid-run. Clear it
      // (persist) and let the job compete for scheduling again this tick,
      // instead of skipping it forever.
      if (job.state.runningAtMs !== null) {
        const stuckMs = now - job.state.runningAtMs;
        if (stuckMs <= this.staleRunningMs) continue; // genuinely still running

        const cleared = patchJobState(job, { runningAtMs: null });
        try {
          await saveJobStore(await this.updateJobInStore(cleared));
        } catch {
          // Persist failed — retry the clear on the next tick rather than
          // running with a stale persisted mark.
          console.warn(
            `[agent-core:cron] stale clear persist failed for job ${job.name} (${job.id}) — will retry next tick`,
          );
          continue;
        }
        console.warn(
          `[agent-core:cron] stale running mark cleared for job ${job.name} (${job.id}) (stuck ${Math.round(stuckMs / 1000)}s) — schedule resumed`,
        );
        job = cleared;
      }

      const nextMs = job.state.nextRunAtMs;
      if (nextMs === null) continue;

      if (nextMs <= now) {
        dueJobs.push(job);
      } else {
        if (soonestNextMs === null || nextMs < soonestNextMs) {
          soonestNextMs = nextMs;
        }
      }
    }

    // Execute due jobs
    for (const job of dueJobs) {
      await this.executeJob(job);
    }

    // If we stopped during execution, don't reschedule
    if (!this.running) return;

    // Schedule next tick
    const delayMs = soonestNextMs
      ? Math.min(Math.max(soonestNextMs - Date.now(), this.tickMs), this.maxTimerDelayMs)
      : this.tickMs;

    this.timer = setTimeout(() => this.scheduleNext(), delayMs);
  }

  private async executeJob(job: CronJob): Promise<void> {
    const startedAt = Date.now();
    const staggerMs = resolveJobStaggerMs(job);

    // Mark running
    job = patchJobState(job, { runningAtMs: startedAt, lastRunAtMs: startedAt });
    try {
      await saveJobStore(await this.updateJobInStore(job));
    } catch {
      // Persistence failure on "running" mark is non-fatal; continue
    }

    // Execute
    let ok = false;
    let errorMsg: string | null = null;
    try {
      const result = this.handler(job);
      if (result instanceof Promise) await result;
      ok = true;
    } catch (err: unknown) {
      errorMsg = err instanceof Error ? err.message : String(err);
    }

    // Settle (sgB fix anchor 2): clear the running mark and roll the schedule.
    // A failure here used to escape executeJob — killing the scheduler loop
    // (unhandled rejection, timer never rescheduled) and/or leaving the job
    // stuck in "running" forever. Contain it: warn + best-effort local clear;
    // the persisted mark is repaired by the stale-running guard (anchor 1).
    try {
      await this.settleJob(job, startedAt, staggerMs, ok, errorMsg);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      job = patchJobState(job, { runningAtMs: null });
      console.warn(
        `[agent-core:cron] settle failed for job ${job.name} (${job.id}): ${message} — mark cleared locally, stale guard will repair persisted state`,
      );
    }
  }

  private async settleJob(
    job: CronJob,
    startedAt: number,
    staggerMs: number,
    ok: boolean,
    errorMsg: string | null,
  ): Promise<void> {
    const endedAt = Date.now();
    const nextRun = computeNextRunAtMs(job.schedule, endedAt, staggerMs);

    // Re-read to avoid stale cache clobbering
    const freshStore = await loadJobStore();
    const freshJob = freshStore[job.id];
    if (!freshJob) return; // deleted during execution (or store read failed — stale guard recovers)

    const updated = patchJobState(freshJob, {
      runningAtMs: null,
      lastRunStatus: ok ? "ok" : "error",
      lastError: errorMsg,
      consecutiveErrors: ok ? 0 : freshJob.state.consecutiveErrors + 1,
      lastDurationMs: endedAt - startedAt,
      runCount: freshJob.state.runCount + 1,
      nextRunAtMs: nextRun,
    });

    await saveJobStore(await this.updateJobInStore(updated));
  }

  private async updateJobInStore(
    job: CronJob,
  ): Promise<Record<string, CronJob>> {
    const jobs = await loadJobStore();
    jobs[job.id] = job;
    return jobs;
  }
}
