"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { Mail, UserPlus } from "lucide-react";
import { Shell } from "@/components/shell";
import { api, getCompanyId } from "@/lib/api";
import { Alert, Badge, Button, Card, EmptyState, Input, Label, PageHeader, Select, Skeleton } from "@/components/ui";

type Member = { id: string; role: string; status: string; user: { first_name: string; last_name: string; email: string } };

export default function TeamPage() {
  const [members, setMembers] = useState<Member[]>([]);
  const [error, setError] = useState("");
  const [showInvite, setShowInvite] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const companyId = getCompanyId();

  const load = useCallback(() => {
    if (!companyId) {
      setIsLoading(false);
      return Promise.resolve();
    }
    setIsLoading(true);
    return api<Member[]>(`/companies/${companyId}/members/`)
      .then(setMembers)
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [companyId]);

  useEffect(() => {
    load();
  }, [load]);

  async function invite(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    try {
      await api(`/companies/${companyId}/invitations/`, {
        method: "POST",
        body: JSON.stringify({ email: f.get("email"), role: f.get("role") }),
      });
      setShowInvite(false);
      alert("Invitation sent.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to invite member");
    }
  }

  async function changeRole(member: Member, role: string) {
    try {
      await api(`/companies/${companyId}/members/${member.id}/`, { method: "PATCH", body: JSON.stringify({ role }) });
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to update member");
    }
  }

  return (
    <Shell>
      <PageHeader
        eyebrow="Workspace"
        title="Team"
        description="Invite the people accountable for delivery."
        action={
          <Button onClick={() => setShowInvite(!showInvite)}>
            <UserPlus className="mr-2 inline" size={16} />
            Invite member
          </Button>
        }
      />
      {error && (
        <Alert variant="error" className="mb-4">
          {error}
        </Alert>
      )}
      {showInvite && (
        <Card className="mb-6 p-5">
          <form onSubmit={invite} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Label className="flex-1">
              Email
              <Input className="mt-1.5" type="email" name="email" required placeholder="colleague@company.com" />
            </Label>
            <Label>
              Role
              <Select name="role" className="mt-1.5">
                <option value="PROJECT_MANAGER">Project manager</option>
                <option value="SITE_MANAGER">Site manager</option>
                <option value="ACCOUNTANT">Accountant</option>
              </Select>
            </Label>
            <Button type="submit">
              <Mail className="mr-2 inline" size={15} />
              Send invite
            </Button>
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
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-[#fafbf9] text-xs uppercase tracking-wide text-[#7b8780]">
                <tr>
                  <th className="px-5 py-3">Member</th>
                  <th className="px-5 py-3">Role</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Manage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#edf0eb]">
                {members.map((m) => (
                  <tr key={m.id}>
                    <td className="px-5 py-4">
                      <p className="font-semibold">
                        {m.user.first_name} {m.user.last_name}
                      </p>
                      <p className="mt-1 text-xs text-[#7b8780]">{m.user.email}</p>
                    </td>
                    <td className="px-5 py-4">
                      <Badge value={m.role} />
                    </td>
                    <td className="px-5 py-4">
                      <Badge value={m.status} />
                    </td>
                    <td className="px-5 py-4">
                      <span className="sr-only">Role for {m.user.email}</span>
                      <Select
                        id={`role-${m.id}`}
                        aria-label={`Role for ${m.user.email}`}
                        value={m.role}
                        onChange={(e) => changeRole(m, e.target.value)}
                        className="px-2 py-1.5 text-xs"
                      >
                        <option value="OWNER">Owner</option>
                        <option value="PROJECT_MANAGER">Project manager</option>
                        <option value="SITE_MANAGER">Site manager</option>
                        <option value="ACCOUNTANT">Accountant</option>
                      </Select>
                    </td>
                  </tr>
                ))}
                {!members.length && (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState title="No members available" description="Invite a colleague to build your workspace." />
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
