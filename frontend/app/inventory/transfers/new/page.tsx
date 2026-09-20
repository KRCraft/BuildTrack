"use client";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/shell";
import { api } from "@/lib/api";
import { Alert, Button, Card, Input, Skeleton } from "@/components/ui";

type Location = { id: string; name: string };
type Material = { id: string; name: string };

type Row = { material: string; quantity_requested: string };

const IDEMPOTENCY_STORAGE_KEY = "buildtrack_transfer_create_idempotency_key";

function getOrCreateIdempotencyKey(): string {
  if (typeof window === "undefined") return crypto.randomUUID();
  const existing = sessionStorage.getItem(IDEMPOTENCY_STORAGE_KEY);
  if (existing) return existing;
  const next = crypto.randomUUID();
  sessionStorage.setItem(IDEMPOTENCY_STORAGE_KEY, next);
  return next;
}

function isValidDecimal(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  // Decimal with up to 4 decimal places, positive, at least 0.0001
  if (!/^\d+(\.\d{1,4})?$/.test(trimmed)) return false;
  const num = Number(trimmed);
  if (!Number.isFinite(num)) return false;
  if (num < 0.0001) return false;
  return true;
}

function hasDuplicateMaterials(rows: Row[]): boolean {
  const ids = rows.map((r) => r.material).filter(Boolean);
  return new Set(ids).size !== ids.length;
}

function Stepper({ current }: { current: 1 | 2 | 3 }) {
  const steps = ["Create", "Dispatch", "Receive"] as const;
  return (
    <ol className="mb-6 flex items-center gap-2" aria-label="Transfer progress">
      {steps.map((label, idx) => {
        const stepNumber = (idx + 1) as 1 | 2 | 3;
        const active = stepNumber === current;
        const completed = stepNumber < current;
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold ${completed ? "bg-moss text-white" : active ? "bg-moss text-white ring-2 ring-moss/20" : "bg-[#edf0eb] text-[#65716a]"}`}
              aria-current={active ? "step" : undefined}
            >
              {idx + 1}
            </span>
            <span className={`text-sm font-semibold ${active ? "text-ink" : completed ? "text-moss" : "text-[#65716a]"}`}>{label}</span>
            {idx < steps.length - 1 && <span className={`mx-2 h-px w-8 ${completed ? "bg-moss" : "bg-[#edf0eb]"}`} aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}

export default function NewTransferPage() {
  const router = useRouter();
  const [locations, setLocations] = useState<Location[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [rows, setRows] = useState<Row[]>([{ material: "", quantity_requested: "" }]);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    Promise.all([api<Location[]>("/inventory/locations/", {}, true), api<Material[]>("/materials/", {}, true)])
      .then(([l, m]) => {
        if (!cancelled) {
          setLocations(l);
          setMaterials(m);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load form data");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function updateRow(index: number, patch: Partial<Row>) {
    setRows((prev) =>
      prev.map((r, i) => {
        if (i !== index) return r;
        const next = { ...r, ...patch };
        // dedup by material: prevent duplicate material selection
        if (patch.material && prev.some((other, oi) => oi !== index && other.material === patch.material)) {
          setFieldError(`Material already added — each material can only appear once.`);
          return r;
        }
        if (patch.material) setFieldError("");
        return next;
      }),
    );
  }

  function addRow() {
    setRows((prev) => [...prev, { material: "", quantity_requested: "" }]);
  }

  function removeRow(index: number) {
    setRows((prev) => prev.filter((_, i) => i !== index));
    setFieldError("");
  }

  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setFieldError("");

    const f = new FormData(e.currentTarget);
    const source = String(f.get("source") || "");
    const destination = String(f.get("destination") || "");
    const purpose = String(f.get("purpose") || "TRANSFER");
    const notes = String(f.get("notes") || "");

    if (!source || !destination) {
      setFieldError("Source and destination are required.");
      return;
    }
    if (source === destination) {
      setFieldError("Source and destination must differ.");
      return;
    }
    if (!rows.length) {
      setFieldError("At least one material is required.");
      return;
    }
    if (hasDuplicateMaterials(rows)) {
      setFieldError("A material can only appear once — dedup by material.");
      return;
    }
    for (const row of rows) {
      if (!row.material) {
        setFieldError("Select a material for each row.");
        return;
      }
      if (!isValidDecimal(row.quantity_requested)) {
        setFieldError(`Invalid quantity "${row.quantity_requested}" — must be a Decimal >= 0.0001 with up to 4 decimal places.`);
        return;
      }
    }

    const payloadItems = rows.map((r) => ({ material: r.material, quantity_requested: r.quantity_requested }));

    const idempotencyKey = getOrCreateIdempotencyKey();

    setIsSaving(true);
    try {
      const data = await api<{ id: string }>(
        "/inventory/transfers/",
        {
          method: "POST",
          headers: { "Idempotency-Key": idempotencyKey },
          body: JSON.stringify({
            source_location: source,
            destination_location: destination,
            purpose,
            notes,
            items: payloadItems,
          }),
        },
        true,
      );
      // success clears idempotency key so next create gets fresh UUID
      if (typeof window !== "undefined") sessionStorage.removeItem(IDEMPOTENCY_STORAGE_KEY);
      router.push(`/inventory/transfers/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to create transfer");
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <Shell>
        <h1 className="mb-2 text-3xl font-bold">New transfer</h1>
        <Stepper current={1} />
        <div className="space-y-3">
          <Skeleton className="h-12" />
          <Skeleton className="h-24" />
          <Skeleton className="h-12" />
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <h1 className="mb-2 text-3xl font-bold">New transfer</h1>
      <p className="mb-4 text-[#65716a]">Create a draft with one or more materials, then dispatch when quantities are confirmed.</p>
      <Stepper current={1} />
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}
      {fieldError && <Alert variant="warning" className="mb-4">{fieldError}</Alert>}
      <Card className="p-6">
        <form onSubmit={save} className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <label className="text-sm font-medium">
              Source location
              <select required name="source" className="mt-1.5 w-full rounded-lg border border-[#d8ded8] bg-white p-2.5 text-sm">
                <option value="">Source location</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm font-medium">
              Destination location
              <select required name="destination" className="mt-1.5 w-full rounded-lg border border-[#d8ded8] bg-white p-2.5 text-sm">
                <option value="">Destination location</option>
                {locations.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm font-medium">
              Purpose
              <select name="purpose" defaultValue="TRANSFER" className="mt-1.5 w-full rounded-lg border border-[#d8ded8] bg-white p-2.5 text-sm">
                <option value="TRANSFER">TRANSFER</option>
                <option value="ALLOCATION">ALLOCATION</option>
                <option value="RETURN">RETURN</option>
              </select>
            </label>
          </div>

          <div className="space-y-3">
            {rows.map((row, index) => (
              <div key={index} className="grid gap-3 sm:grid-cols-[1fr_220px_auto]">
                <select
                  required
                  value={row.material}
                  onChange={(e) => updateRow(index, { material: e.target.value })}
                  className="rounded-lg border border-[#d8ded8] bg-white p-2.5 text-sm"
                  aria-label={`Material row ${index + 1}`}
                >
                  <option value="">Material</option>
                  {materials.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </select>
                <Input
                  required
                  type="text"
                  inputMode="decimal"
                  value={row.quantity_requested}
                  onChange={(e) => updateRow(index, { quantity_requested: e.target.value })}
                  placeholder="Quantity (e.g. 10.0000)"
                  aria-label={`Quantity row ${index + 1}`}
                />
                {rows.length > 1 && (
                  <button type="button" onClick={() => removeRow(index)} className="text-sm font-semibold text-clay hover:underline">
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>

          <button type="button" onClick={addRow} className="text-sm font-semibold text-moss hover:underline">
            + Add material
          </button>

          <Input name="notes" placeholder="Notes" aria-label="Notes" />

          <Button type="submit" loading={isSaving} disabled={isSaving}>
            {isSaving ? "Creating…" : "Create draft transfer"}
          </Button>
        </form>
      </Card>
    </Shell>
  );
}
