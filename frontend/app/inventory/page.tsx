"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Shell } from "@/components/shell";
import { api } from "@/lib/api";
import { Alert, Badge, Button, Card, EmptyState, Input, Label, PageHeader, Select, Skeleton } from "@/components/ui";

type Balance = { id: string; material: string; material_name: string; unit: string; location: string; location_name: string; project_name: string | null; quantity_on_hand: string; minimum_stock_level: string; low_stock: boolean };
type Location = { id: string; name: string; location_type: string };
type Material = { id: string; name: string };

export default function InventoryPage() {
  const [balances, setBalances] = useState<Balance[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [low, setLow] = useState(false);
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const query = low ? "?low_stock=true" : "";
      const [b, l, m] = await Promise.all([
        api<Balance[]>(`/inventory/balances/${query}`, {}, true),
        api<Location[]>("/inventory/locations/", {}, true),
        api<Material[]>("/materials/", {}, true),
      ]);
      setBalances(b);
      setLocations(l);
      setMaterials(m);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load inventory");
    } finally {
      setIsLoading(false);
    }
  }, [low]);

  useEffect(() => {
    load();
  }, [load]);

  async function receive(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api(
        "/inventory/receipts/",
        {
          method: "POST",
          body: JSON.stringify({
            location: f.get("location"),
            material: f.get("material"),
            quantity: f.get("quantity"),
            reason: f.get("reason"),
          }),
        },
        true
      );
      setShow(false);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to receive stock");
    }
  }

  return (
    <Shell>
      <PageHeader
        title="Inventory"
        description="Stock by warehouse and project site. Low stock uses company-wide material totals."
        action={
          <div className="flex gap-3">
            <Link href="/inventory/transfers/new">
              <Button variant="secondary">Transfer material</Button>
            </Link>
            <Button onClick={() => setShow(!show)}>Receive stock</Button>
          </div>
        }
      />
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {show && (
        <Card className="mb-6 p-5">
          <form onSubmit={receive} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Label>
              Destination location
              <Select name="location" required className="mt-1.5">
                <option value="">Destination location</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </Select>
            </Label>
            <Label>
              Material
              <Select name="material" required className="mt-1.5">
                <option value="">Material</option>
                {materials.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </Select>
            </Label>
            <Label>
              Quantity
              <Input name="quantity" type="number" min="0.0001" step="0.0001" placeholder="Quantity" required className="mt-1.5" />
            </Label>
            <Label>
              Delivery note
              <Input name="reason" placeholder="Delivery note" className="mt-1.5" />
            </Label>
            <div className="flex items-end">
              <Button type="submit">Record receipt</Button>
            </div>
          </form>
        </Card>
      )}
      <Card>
        <div className="flex gap-3 border-b border-[#edf0eb] p-4">
          <Label className="flex items-center gap-2 !font-normal">
            <input type="checkbox" checked={low} onChange={(e) => setLow(e.target.checked)} /> Low stock only
          </Label>
        </div>
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
                  <th className="px-5 py-3">Location</th>
                  <th className="px-5 py-3">Project</th>
                  <th className="px-5 py-3">On hand</th>
                  <th className="px-5 py-3">Minimum</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf0eb]">
                {balances.map((b) => (
                  <tr key={b.id}>
                    <td className="px-5 py-4 font-semibold">
                      {b.material_name}
                      <span className="ml-2 text-xs text-[#78847d]">{b.unit}</span>
                    </td>
                    <td className="px-5 py-4">{b.location_name}</td>
                    <td className="px-5 py-4">{b.project_name || "—"}</td>
                    <td className="px-5 py-4">{b.quantity_on_hand}</td>
                    <td className="px-5 py-4">{b.minimum_stock_level}</td>
                    <td className="px-5 py-4">
                      <Badge value={b.low_stock ? "LOW STOCK" : "IN STOCK"} />
                    </td>
                  </tr>
                ))}
                {!balances.length && (
                  <tr>
                    <td colSpan={6}>
                      <EmptyState title="No inventory balances yet" description="Stock will appear once materials are received." />
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
