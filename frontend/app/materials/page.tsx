"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Shell } from "@/components/shell";
import { api } from "@/lib/api";
import { Alert, Badge, Button, Card, EmptyState, Input, Label, PageHeader, Select, Skeleton } from "@/components/ui";

type Material = { id: string; code: string; name: string; category: string; unit: string; minimum_stock_level: string; total_stock: string; low_stock: boolean; is_active: boolean };

export default function MaterialsPage() {
  const [items, setItems] = useState<Material[]>([]);
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(() => {
    setIsLoading(true);
    return api<Material[]>("/materials/", {}, true)
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
        "/materials/",
        {
          method: "POST",
          body: JSON.stringify({
            code: f.get("code"),
            name: f.get("name"),
            category: f.get("category"),
            unit: f.get("unit"),
            minimum_stock_level: f.get("minimum_stock_level") || 0,
          }),
        },
        true
      );
      setShow(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save material");
    }
  }

  async function deactivate(id: string) {
    if (!confirm("Deactivate this material?")) return;
    await api(`/materials/${id}/`, { method: "PATCH", body: JSON.stringify({ is_active: false }) }, true);
    load();
  }

  return (
    <Shell>
      <PageHeader
        title="Materials"
        description="Standardized construction materials and company-wide stock thresholds."
        action={<Button onClick={() => setShow(!show)}>New material</Button>}
      />
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {show && (
        <Card className="mb-6 p-5">
          <form onSubmit={save} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Label>
              Material code
              <Input name="code" placeholder="Material code" required className="mt-1.5" />
            </Label>
            <Label>
              Material name
              <Input name="name" placeholder="Material name" required className="mt-1.5" />
            </Label>
            <Label>
              Category
              <Input name="category" placeholder="Category" className="mt-1.5" />
            </Label>
            <Label>
              Unit
              <Select name="unit" className="mt-1.5">
                <option>PIECE</option>
                <option>KG</option>
                <option>TON</option>
                <option>METER</option>
                <option>M2</option>
                <option>M3</option>
                <option>LITER</option>
                <option>BAG</option>
                <option>BOX</option>
                <option>OTHER</option>
              </Select>
            </Label>
            <Label>
              Minimum stock
              <Input name="minimum_stock_level" type="number" min="0" step="0.0001" placeholder="Minimum stock" className="mt-1.5" />
            </Label>
            <div className="flex items-end">
              <Button type="submit">Save material</Button>
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
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-[#fafbf9] text-xs uppercase tracking-wide text-[#7b8780]">
                <tr>
                  <th className="px-5 py-3">Material</th>
                  <th className="px-5 py-3">Category</th>
                  <th className="px-5 py-3">Unit</th>
                  <th className="px-5 py-3">Total stock</th>
                  <th className="px-5 py-3">Minimum</th>
                  <th className="px-5 py-3">Status</th>
                  <th />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf0eb]">
                {items.map((m) => (
                  <tr key={m.id}>
                    <td className="px-5 py-4 font-semibold">
                      {m.name}
                      <span className="ml-2 text-xs text-[#78847d]">{m.code}</span>
                    </td>
                    <td className="px-5 py-4">{m.category || "—"}</td>
                    <td className="px-5 py-4">{m.unit}</td>
                    <td className="px-5 py-4">{m.total_stock}</td>
                    <td className="px-5 py-4">{m.minimum_stock_level}</td>
                    <td className="px-5 py-4">
                      <Badge value={m.low_stock ? "LOW STOCK" : m.is_active ? "ACTIVE" : "INACTIVE"} />
                    </td>
                    <td className="px-5 py-4">
                      {m.is_active && (
                        <Button variant="ghost" size="sm" onClick={() => deactivate(m.id)}>
                          Deactivate
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
                {!items.length && (
                  <tr>
                    <td colSpan={7}>
                      <EmptyState title="No materials yet" description="Create a material to start tracking stock." />
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
