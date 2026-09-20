"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Shell } from "@/components/shell";
import { api } from "@/lib/api";
import { Alert, Badge, Button, Card, EmptyState, Input, Label, PageHeader, Skeleton } from "@/components/ui";

type Supplier = { id: string; name: string; tax_id: string; phone: string; email: string; address: string; is_active: boolean };

export default function SuppliersPage() {
  const [items, setItems] = useState<Supplier[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(() => {
    setIsLoading(true);
    return api<Supplier[]>("/suppliers/", {}, true)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api(
        "/suppliers/",
        {
          method: "POST",
          body: JSON.stringify({
            name: f.get("name"),
            tax_id: f.get("tax_id"),
            phone: f.get("phone"),
            email: f.get("email"),
            address: f.get("address"),
          }),
        },
        true
      );
      setOpen(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to create supplier");
    }
  }

  async function deactivate(s: Supplier) {
    if (!confirm(`Deactivate ${s.name}?`)) return;
    try {
      await api(`/suppliers/${s.id}/`, { method: "PATCH", body: JSON.stringify({ is_active: false }) }, true);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to update supplier");
    }
  }

  return (
    <Shell>
      <PageHeader
        title="Suppliers"
        description="Maintain the vendors available for project expense records."
        action={<Button onClick={() => setOpen(!open)}>New supplier</Button>}
      />
      {error && (
        <Alert variant="error" className="mb-5">
          {error}
        </Alert>
      )}
      {open && (
        <Card className="mb-6 p-5">
          <form onSubmit={save} className="grid gap-4 sm:grid-cols-2">
            <Label>
              Supplier name
              <Input className="mt-1.5" name="name" required />
            </Label>
            <Label>
              Tax ID
              <Input className="mt-1.5" name="tax_id" />
            </Label>
            <Label>
              Phone
              <Input className="mt-1.5" name="phone" />
            </Label>
            <Label>
              Email
              <Input className="mt-1.5" name="email" type="email" />
            </Label>
            <Label className="sm:col-span-2">
              Address
              <Input className="mt-1.5" name="address" />
            </Label>
            <div className="sm:col-span-2">
              <Button type="submit">Save supplier</Button>
            </div>
          </form>
        </Card>
      )}
      <Card>
        {isLoading ? (
          <div className="space-y-3 p-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-[#fafbf9] text-xs uppercase tracking-wide text-[#7b8780]">
                <tr>
                  <th className="px-5 py-3">Supplier</th>
                  <th className="px-5 py-3">Tax ID</th>
                  <th className="px-5 py-3">Contact</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf0eb]">
                {items.map((s) => (
                  <tr key={s.id}>
                    <td className="px-5 py-4 font-semibold">{s.name}</td>
                    <td className="px-5 py-4">{s.tax_id || "—"}</td>
                    <td className="px-5 py-4 text-[#65716a]">{s.email || s.phone || "—"}</td>
                    <td className="px-5 py-4">
                      <Badge value={s.is_active ? "ACTIVE" : "INACTIVE"} />
                    </td>
                    <td className="px-5 py-4">
                      {s.is_active && (
                        <Button variant="ghost" size="sm" onClick={() => deactivate(s)}>
                          Deactivate
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {!items.length && (
                  <tr>
                    <td colSpan={5}>
                      <EmptyState title="No suppliers recorded" description="Add a supplier to reference it in expenses." />
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
