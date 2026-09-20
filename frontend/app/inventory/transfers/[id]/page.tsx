"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Shell } from "@/components/shell";
import { api } from "@/lib/api";
import { Alert, Badge, Button, Card, Input, Skeleton } from "@/components/ui";

type Item = {
  id: string;
  material_name: string;
  quantity_requested: string;
  quantity_dispatched: string;
  quantity_received: string;
};
type Transfer = {
  id: string;
  source_name: string;
  destination_name: string;
  purpose: string;
  status: string;
  notes: string;
  items: Item[];
};

function isValidDecimal(value: string): boolean {
  const trimmed = value.trim();
  if (!trimmed) return false;
  if (!/^\d+(\.\d{1,4})?$/.test(trimmed)) return false;
  const num = Number(trimmed);
  return Number.isFinite(num) && num > 0;
}

function getOrCreateIdempotencyKey(storageKey: string): string {
  if (typeof window === "undefined") return crypto.randomUUID();
  const existing = sessionStorage.getItem(storageKey);
  if (existing) return existing;
  const next = crypto.randomUUID();
  sessionStorage.setItem(storageKey, next);
  return next;
}

function Stepper({ status }: { status: string }) {
  // Map backend status to step index: Create -> Dispatch -> Receive
  const order: Record<string, number> = {
    DRAFT: 1,
    DISPATCHED: 2,
    PARTIALLY_RECEIVED: 2,
    RECEIVED: 3,
    CANCELLED: 1,
  };
  const current = order[status] ?? 1;
  const steps = ["Create", "Dispatch", "Receive"] as const;
  return (
    <ol className="mb-6 flex items-center gap-2" aria-label="Transfer progress">
      {steps.map((label, idx) => {
        const stepNumber = idx + 1;
        const active = stepNumber === current;
        const completed = stepNumber < current || status === "RECEIVED";
        const isCancelled = status === "CANCELLED";
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={`grid h-7 w-7 place-items-center rounded-full text-xs font-bold ${isCancelled && stepNumber === 1 ? "bg-amber-500 text-white" : completed ? "bg-moss text-white" : active ? "bg-moss text-white ring-2 ring-moss/20" : "bg-[#edf0eb] text-[#65716a]"}`}
              aria-current={active ? "step" : undefined}
            >
              {stepNumber}
            </span>
            <span className={`text-sm font-semibold ${active ? "text-ink" : completed ? "text-moss" : "text-[#65716a]"}`}>{label}</span>
            {idx < steps.length - 1 && <span className={`mx-2 h-px w-8 ${completed ? "bg-moss" : "bg-[#edf0eb]"}`} aria-hidden />}
          </li>
        );
      })}
    </ol>
  );
}

export default function TransferDetail() {
  const { id } = useParams<{ id: string }>();
  const [transfer, setTransfer] = useState<Transfer | null>(null);
  const [error, setError] = useState("");
  const [fieldError, setFieldError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [dispatchPending, setDispatchPending] = useState(false);
  const [cancelPending, setCancelPending] = useState(false);
  const [receivePending, setReceivePending] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await api<Transfer>(`/inventory/transfers/${id}/`, {}, true);
      setTransfer(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load transfer");
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function action(name: string, body: unknown = {}, idempotencyKey?: string) {
    setError("");
    setFieldError("");
    const headers: Record<string, string> = {};
    if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
    try {
      await api(`/inventory/transfers/${id}/${name}/`, { method: "POST", headers, body: JSON.stringify(body) }, true);
      // clear idempotency key on success to allow fresh retry if needed but backend will return same on duplicate
      if (typeof window !== "undefined" && idempotencyKey) {
        if (name === "dispatch") sessionStorage.removeItem(`buildtrack_transfer_dispatch_${id}`);
        if (name === "receive") sessionStorage.removeItem(`buildtrack_transfer_receive_${id}`);
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
      throw e;
    }
  }

  async function handleDispatch() {
    setDispatchPending(true);
    const key = getOrCreateIdempotencyKey(`buildtrack_transfer_dispatch_${id}`);
    // crypto.randomUUID already used via getOrCreateIdempotencyKey
    // also ensure Idempotency-Key header is sent
    try {
      await action("dispatch", {}, key);
    } finally {
      setDispatchPending(false);
    }
  }

  async function handleCancel() {
    setCancelPending(true);
    try {
      await action("cancel", {});
    } finally {
      setCancelPending(false);
    }
  }

  function handleReceive(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!transfer) return;
    setFieldError("");
    setError("");
    const f = new FormData(e.currentTarget);
    const items: { id: string; quantity: string }[] = [];
    for (const item of transfer.items) {
      const raw = String(f.get(item.id) || "").trim();
      if (!raw) continue;
      if (!isValidDecimal(raw)) {
        setFieldError(`Invalid quantity "${raw}" for ${item.material_name} — must be Decimal >0 with up to 4 decimals.`);
        return;
      }
      const remaining = Number(item.quantity_dispatched) - Number(item.quantity_received);
      if (Number(raw) > remaining + 1e-9) {
        setFieldError(`Cannot receive more than dispatched for ${item.material_name}. Remaining ${remaining}.`);
        return;
      }
      // Decimal validation passed
      items.push({ id: item.id, quantity: raw });
    }
    if (!items.length) {
      setFieldError("Enter at least one receive quantity (Decimal validation).");
      return;
    }
    // dedup by material is inherent because items are by id, but ensure no duplicate ids
    const seen = new Set(items.map((i) => i.id));
    if (seen.size !== items.length) {
      setFieldError("Duplicate material in receive payload.");
      return;
    }
    const key = getOrCreateIdempotencyKey(`buildtrack_transfer_receive_${id}`);
    setReceivePending(true);
    action("receive", { items }, key).finally(() => setReceivePending(false));
  }

  if (isLoading) {
    return (
      <Shell>
        <Skeleton className="mb-4 h-8 w-64" />
        <Skeleton className="mb-6 h-6 w-32" />
        <Skeleton className="h-64" />
        <p className="mt-4 text-sm text-[#65716a]">Loading transfer…</p>
      </Shell>
    );
  }

  if (!transfer) {
    return (
      <Shell>
        <Alert variant="error">{error || "Transfer not found."}</Alert>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {transfer.source_name} → {transfer.destination_name}
          </h1>
          <p className="mt-2 text-[#65716a]">{transfer.purpose} transfer</p>
        </div>
        <Badge value={transfer.status} />
      </div>
      <Stepper status={transfer.status} />
      {error && <Alert variant="error" className="mb-4">{error}</Alert>}
      {fieldError && <Alert variant="warning" className="mb-4">{fieldError}</Alert>}
      <Card>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#fafbf9] text-xs uppercase tracking-wide text-[#7b8780]">
              <tr>
                <th className="p-4">Material</th>
                <th className="p-4">Requested</th>
                <th className="p-4">Dispatched</th>
                <th className="p-4">Received</th>
              </tr>
            </thead>
            <tbody>
              {transfer.items.map((i) => (
                <tr key={i.id} className="border-t border-[#edf0eb]">
                  <td className="p-4 font-semibold">{i.material_name}</td>
                  <td className="p-4">{i.quantity_requested}</td>
                  <td className="p-4">{i.quantity_dispatched}</td>
                  <td className="p-4">{i.quantity_received}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="border-t border-[#edf0eb] p-5">
          {transfer.status === "DRAFT" && (
            <div className="flex gap-3">
              <Button onClick={handleDispatch} loading={dispatchPending} disabled={dispatchPending || cancelPending}>
                {dispatchPending ? "Dispatching…" : "Dispatch"}
              </Button>
              <Button variant="secondary" onClick={handleCancel} loading={cancelPending} disabled={dispatchPending || cancelPending}>
                {cancelPending ? "Cancelling…" : "Cancel"}
              </Button>
            </div>
          )}
          {["DISPATCHED", "PARTIALLY_RECEIVED"].includes(transfer.status) && (
            <form onSubmit={handleReceive} className="space-y-3">
              <p className="font-semibold">Receive quantities</p>
              <p className="text-sm text-[#65716a]">Decimal validation: up to 4 decimal places, must be &gt;0 and ≤ remaining dispatched.</p>
              {transfer.items.map((i) => {
                const remaining = Number(i.quantity_dispatched) - Number(i.quantity_received);
                const disabled = remaining <= 0;
                return (
                  <label key={i.id} className="flex items-center gap-3 text-sm">
                    <span className="w-40 font-medium">{i.material_name}</span>
                    <Input
                      name={i.id}
                      type="text"
                      inputMode="decimal"
                      placeholder={disabled ? "Fully received" : `Remaining ${remaining}`}
                      disabled={disabled || receivePending}
                      aria-label={`Receive quantity for ${i.material_name}`}
                    />
                  </label>
                );
              })}
              <Button type="submit" loading={receivePending} disabled={receivePending}>
                {receivePending ? "Recording…" : "Record receipt"}
              </Button>
            </form>
          )}
          {transfer.status === "RECEIVED" && <p className="text-sm font-semibold text-moss">Transfer complete — all quantities received.</p>}
          {transfer.status === "CANCELLED" && <p className="text-sm font-semibold text-amber-700">Transfer cancelled.</p>}
        </div>
      </Card>
    </Shell>
  );
}
