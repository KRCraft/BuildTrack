"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Shell } from "@/components/shell";
import { api, Project } from "@/lib/api";
import { Alert, Badge, Button, Card, EmptyState, Input, Label, PageHeader, Select, Skeleton } from "@/components/ui";

type Supplier = { id: string; name: string };
type Category = { id: string; name: string; code: string };
type Expense = { id: string; project_name: string; category_name: string; supplier_name: string | null; amount: string; expense_date: string; payment_method: string; status: string; description: string };
type Results = { results: Expense[] };

export function ExpensesPage({ projectId }: { projectId?: string }) {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [project, setProject] = useState(projectId || "");
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const [show, setShow] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const query = new URLSearchParams();
      if (project) query.set("project_id", project);
      if (filter) query.set("status", filter);
      const [list, allProjects, allSuppliers] = await Promise.all([
        api<Results>(`/expenses/?${query}`, {}, true),
        api<Project[]>("/projects/", {}, true),
        api<Supplier[]>("/suppliers/", {}, true),
      ]);
      setExpenses(list.results);
      setProjects(allProjects);
      setSuppliers(allSuppliers);
      if (project) {
        const budget = await api<{ active_version: { categories: Category[] } | null }>(`/projects/${project}/budget/`, {}, true);
        setCategories(budget?.active_version?.categories || []);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load expenses");
    } finally {
      setIsLoading(false);
    }
  }, [project, filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function action(id: string, name: string) {
    if (["approve", "reject", "reverse"].includes(name) && !confirm(`${name} this expense?`)) return;
    try {
      await api(`/expenses/${id}/${name}/`, { method: "POST", body: "{}" }, true);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    }
  }

  async function create(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api(
        "/expenses/",
        {
          method: "POST",
          body: JSON.stringify({
            project: f.get("project"),
            budget_category: f.get("budget_category"),
            supplier: f.get("supplier") || null,
            amount: f.get("amount"),
            currency_code: "UZS",
            expense_date: f.get("expense_date"),
            payment_method: f.get("payment_method"),
            description: f.get("description"),
          }),
        },
        true
      );
      setShow(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create expense");
    }
  }

  return (
    <Shell>
      <PageHeader
        eyebrow={projectId ? "Project overview" : undefined}
        title="Expenses"
        description="Track cost requests and preserve the approval trail."
        action={<Button onClick={() => setShow(!show)}>Create expense</Button>}
      />
      {projectId && (
        <Link href={`/projects/${projectId}`} className="mb-4 inline-flex text-sm font-semibold text-moss">
          ← Project overview
        </Link>
      )}
      {error && (
        <Alert variant="error" className="mb-5">
          {error}
        </Alert>
      )}
      {show && (
        <Card className="mb-6 p-5">
          <form onSubmit={create} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Label>
              Project
              <Select required name="project" value={project} onChange={(e) => setProject(e.target.value)} className="mt-1.5">
                <option value="">Select project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </Label>
            <Label>
              Budget category
              <Select required name="budget_category" className="mt-1.5">
                <option value="">Select category</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.code} — {c.name}
                  </option>
                ))}
              </Select>
            </Label>
            <Label>
              Supplier
              <Select name="supplier" className="mt-1.5">
                <option value="">No supplier</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Label>
            <Label>
              Amount
              <Input className="mt-1.5" name="amount" type="number" min="0.0001" step="0.0001" required />
            </Label>
            <Label>
              Expense date
              <Input className="mt-1.5" name="expense_date" type="date" required />
            </Label>
            <Label>
              Payment method
              <Select name="payment_method" className="mt-1.5">
                <option>CASH</option>
                <option>BANK_TRANSFER</option>
                <option>CARD</option>
                <option>OTHER</option>
              </Select>
            </Label>
            <Label className="sm:col-span-2 lg:col-span-3">
              Description
              <Input className="mt-1.5" name="description" />
            </Label>
            <div className="flex items-end">
              <Button type="submit">Save draft</Button>
            </div>
          </form>
        </Card>
      )}
      <Card>
        <div className="flex gap-3 border-b border-[#edf0eb] p-4">
          <span className="sr-only">Filter by project</span>
          <Select
            id="filter-project"
            value={project}
            disabled={!!projectId}
            onChange={(e) => setProject(e.target.value)}
            className="max-w-[200px]"
            aria-label="Filter by project"
          >
            <option value="">All projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
          <span className="sr-only">Filter by status</span>
          <Select
            id="filter-status"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="max-w-[200px]"
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            {["DRAFT", "PENDING_APPROVAL", "APPROVED", "REJECTED", "CANCELLED"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </Select>
        </div>
        {isLoading ? (
          <div className="space-y-3 p-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-sm">
              <thead className="bg-[#fafbf9] text-xs uppercase tracking-wide text-[#7b8780]">
                <tr>
                  <th className="px-5 py-3">Expense</th>
                  <th className="px-5 py-3">Project / category</th>
                  <th className="px-5 py-3">Supplier</th>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3">Amount</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf0eb]">
                {expenses.map((x) => (
                  <tr key={x.id}>
                    <td className="px-5 py-4 font-medium">
                      {x.description || "Untitled expense"}
                      <span className="mt-1 block text-xs text-[#78847d]">{x.payment_method.replace("_", " ")}</span>
                    </td>
                    <td className="px-5 py-4">
                      {x.project_name}
                      <span className="mt-1 block text-xs text-[#78847d]">{x.category_name}</span>
                    </td>
                    <td className="px-5 py-4">{x.supplier_name || "—"}</td>
                    <td className="px-5 py-4">{x.expense_date}</td>
                    <td className="px-5 py-4 font-semibold">{Number(x.amount).toLocaleString()}</td>
                    <td className="px-5 py-4">
                      <Badge value={x.status} />
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex gap-2">
                        {x.status === "DRAFT" && (
                          <Button size="sm" onClick={() => action(x.id, "submit")}>
                            Submit
                          </Button>
                        )}
                        {x.status === "PENDING_APPROVAL" && (
                          <>
                            <Button size="sm" onClick={() => action(x.id, "approve")}>
                              Approve
                            </Button>
                            <Button variant="danger" size="sm" onClick={() => action(x.id, "reject")}>
                              Reject
                            </Button>
                          </>
                        )}
                        {x.status === "APPROVED" && (
                          <Button variant="secondary" size="sm" onClick={() => action(x.id, "reverse")}>
                            Reverse
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!expenses.length && (
                  <tr>
                    <td colSpan={7}>
                      <EmptyState title="No expenses match this view" description="Try adjusting filters or create a new expense." />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </Shell>
  );
}
