"use client";

import { useEffect, useState } from "react";

import { Button, fieldClass } from "@/components/button";
import { CRM_SECTIONS, SectionNav } from "@/components/section-nav";
import { api, type Me, type TaskItem, type TaskPage, type TeamMember } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function TasksPage() {
  const { token } = useAuth();
  const [page, setPage] = useState<TaskPage | null>(null);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [title, setTitle] = useState("");
  const [dueOn, setDueOn] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [canWrite, setCanWrite] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load(activeToken: string, overdue: boolean) {
    const query = overdue ? "/api/v1/tasks?page_size=100&overdue=true" : "/api/v1/tasks?page_size=100";
    api<TaskPage>(query, activeToken)
      .then(setPage)
      .catch((reason: Error) => setError(reason.message));
  }

  useEffect(() => {
    if (!token) return;
    load(token, overdueOnly);
    api<Me>("/api/v1/me", token)
      .then((me) => setCanWrite(me.role !== "read_only"))
      .catch(() => setCanWrite(false));
    api<TeamMember[]>("/api/v1/team", token)
      .then(setTeam)
      .catch(() => setTeam([]));
  }, [token, overdueOnly]);

  const names = new Map(team.map((member) => [member.user_id, member.display_name]));

  return (
    <section className="max-w-3xl">
      <h1 className="text-4xl font-bold md:text-5xl">Follow-ups</h1>
      <SectionNav label="CRM" items={CRM_SECTIONS} />
      <p className="mt-4 text-lg leading-8">
        A due date is the follow-up. Overdue is calculated in India time when this list loads.
        Nothing on this screen places a call.
      </p>
      {error ? <p className="mt-6" role="alert">{error}</p> : null}
      <div className="mt-8 flex gap-3">
        <button
          type="button"
          className={`text-sm font-medium text-muted-foreground ${overdueOnly ? "" : "underline"}`}
          onClick={() => setOverdueOnly(false)}
        >
          All
        </button>
        <button
          type="button"
          className={`text-sm font-medium text-muted-foreground ${overdueOnly ? "underline" : ""}`}
          onClick={() => setOverdueOnly(true)}
        >
          Overdue
        </button>
      </div>
      {!page && !error ? <p className="mt-10">Loading</p> : null}
      {page && page.total === 0 ? (
        <p className="mt-10 bg-muted rounded-xl p-8 text-lg">{overdueOnly ? "No overdue tasks." : "No tasks."}</p>
      ) : null}
      {page && page.items.length > 0 ? (
        <ul className="mt-8 grid gap-3">
          {page.items.map((task) => (
            <li key={task.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-border py-3">
              <div>
                <p className={task.status === "done" ? "line-through" : "font-bold"}>{task.title}</p>
                <p className="text-sm">
                  {task.status}
                  {task.due_on ? ` · due ${task.due_on}` : ""}
                  {task.overdue ? " · overdue" : ""}
                  {task.owner_user_id ? ` · ${names.get(task.owner_user_id) ?? "assigned"}` : " · unassigned"}
                </p>
              </div>
              {canWrite && task.status === "open" ? (
                <button
                  type="button"
                  className="text-sm font-medium text-muted-foreground"
                  onClick={() => {
                    if (!token) return;
                    api<TaskItem>(`/api/v1/tasks/${task.id}`, token, {
                      method: "PATCH",
                      body: JSON.stringify({ status: "done" }),
                    })
                      .then(() => load(token, overdueOnly))
                      .catch((reason: Error) => setError(reason.message));
                  }}
                >
                  Mark done
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
      {canWrite ? (
        <form
          className="mt-8 grid gap-3"
          onSubmit={(event) => {
            event.preventDefault();
            if (!token || !title.trim()) return;
            const body: { title: string; due_on?: string; owner_user_id?: string } = { title };
            if (dueOn) body.due_on = dueOn;
            if (ownerId) body.owner_user_id = ownerId;
            api<TaskItem>("/api/v1/tasks", token, {
              method: "POST",
              body: JSON.stringify(body),
            })
              .then(() => {
                setTitle("");
                setDueOn("");
                load(token, overdueOnly);
              })
              .catch((reason: Error) => setError(reason.message));
          }}
        >
          <input className={`${fieldClass} max-w-md`} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Follow-up" required />
          <input className={`${fieldClass} max-w-md`} type="date" value={dueOn} onChange={(event) => setDueOn(event.target.value)} aria-label="Due date" />
          <select className={`${fieldClass} max-w-md`} value={ownerId} onChange={(event) => setOwnerId(event.target.value)} aria-label="Owner">
            <option value="">Assign to me</option>
            {team.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {member.display_name}
              </option>
            ))}
          </select>
          <div>
            <Button type="submit" tone="ink">Add follow-up</Button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
