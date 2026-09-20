"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell } from "@/components/shell";
import { api, Company, getCompanyId, setCompanyId } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import { Alert, Button, Card, CardBody, CardHeader, Input, Label } from "@/components/ui";

type Me = { id: string; email: string; first_name: string; last_name: string };

function isThrottleError(message: string): boolean {
  const lower = message.toLowerCase();
  return lower.includes("429") || lower.includes("throttled") || lower.includes("too many") || lower.includes("try again");
}

export default function SettingsPage() {
  const { user, companies, refresh } = useAuth();
  const router = useRouter();
  const current = companies.find((c) => c.id === getCompanyId());

  // Company workspace state
  const [companyError, setCompanyError] = useState("");
  const [companyMessage, setCompanyMessage] = useState("");
  const [companyPending, setCompanyPending] = useState(false);

  // Profile state
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [profileError, setProfileError] = useState("");
  const [profileMessage, setProfileMessage] = useState("");
  const [profilePending, setProfilePending] = useState(false);

  // Password state
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordPending, setPasswordPending] = useState(false);

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name ?? "");
      setLastName(user.last_name ?? "");
    }
  }, [user]);

  async function handleProfileSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setProfileError("");
    setProfileMessage("");
    if (!firstName.trim() && !lastName.trim()) {
      setProfileError("Please provide a first or last name.");
      return;
    }
    setProfilePending(true);
    try {
      await api<Me>("/auth/me/", {
        method: "PATCH",
        body: JSON.stringify({ first_name: firstName.trim(), last_name: lastName.trim() }),
      });
      await refresh();
      setProfileMessage("Profile updated.");
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : "Unable to update profile.");
    } finally {
      setProfilePending(false);
    }
  }

  async function handlePasswordSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setPasswordError("");
    setPasswordMessage("");

    if (!oldPassword || !newPassword || !confirmPassword) {
      setPasswordError("All password fields are required.");
      return;
    }
    if (newPassword.length < 10) {
      setPasswordError("New password must be at least 10 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.");
      return;
    }

    setPasswordPending(true);
    try {
      const res = await api<{ detail: string }>("/auth/password/change/", {
        method: "POST",
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
          new_password_confirm: confirmPassword,
        }),
      });
      setPasswordMessage(res?.detail ?? "Password updated. Please log in again.");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      // Server blacklists refresh tokens and clears cookie; force re-auth after short delay
      setTimeout(async () => {
        try {
          await api<void>("/auth/logout/", { method: "POST" });
        } catch {
          // ignore
        }
        // Clear local access token via auth provider signOut would, but we do minimal
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("buildtrack:auth-expired"));
        }
        router.push("/login");
      }, 1200);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to change password.";
      if (isThrottleError(msg)) {
        setPasswordError("Too many attempts. Please wait a minute and try again. (429)");
      } else {
        setPasswordError(msg);
      }
    } finally {
      setPasswordPending(false);
    }
  }

  async function handleCreateCompany(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setCompanyError("");
    setCompanyMessage("");
    setCompanyPending(true);
    const f = new FormData(e.currentTarget);
    try {
      const company = await api<Company>("/companies/", {
        method: "POST",
        body: JSON.stringify({
          name: f.get("name"),
          slug: f.get("slug") || undefined,
          currency_code: f.get("currency_code"),
          timezone: f.get("timezone"),
        }),
      });
      setCompanyId(company.id);
      await refresh();
      setCompanyMessage("Company workspace created.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to create company.";
      if (isThrottleError(msg)) setCompanyError("Too many requests. Please try again later.");
      else setCompanyError(msg);
    } finally {
      setCompanyPending(false);
    }
  }

  async function handleUpdateCompany(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!current) return;
    setCompanyError("");
    setCompanyMessage("");
    setCompanyPending(true);
    const f = new FormData(e.currentTarget);
    try {
      await api(`/companies/${current.id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          name: f.get("name"),
          currency_code: f.get("currency_code"),
          timezone: f.get("timezone"),
        }),
      });
      await refresh();
      setCompanyMessage("Settings saved.");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unable to save settings.";
      if (isThrottleError(msg)) setCompanyError("Too many requests. Please try again later.");
      else setCompanyError(msg);
    } finally {
      setCompanyPending(false);
    }
  }

  return (
    <Shell>
      <div className="mb-7">
        <p className="text-sm font-semibold text-moss">Workspace</p>
        <h1 className="mt-1 text-3xl font-bold">Settings</h1>
        <p className="mt-2 text-[#65716a]">Manage your profile, security, and company defaults.</p>
      </div>

      <div className="grid gap-6 max-w-3xl">
        {/* Profile */}
        <Card>
          <CardHeader>
            <div>
              <h2 className="text-base font-semibold">Profile</h2>
              <p className="text-sm text-[#65716a]">Update your name. Email is managed by your account.</p>
            </div>
          </CardHeader>
          <CardBody>
            {profileError && <Alert variant="error" className="mb-4">{profileError}</Alert>}
            {profileMessage && <Alert variant="success" className="mb-4">{profileMessage}</Alert>}
            <form onSubmit={handleProfileSubmit} className="grid gap-4 sm:grid-cols-2">
              <Label>
                Email
                <Input className="mt-1.5" value={user?.email ?? ""} disabled aria-disabled />
              </Label>
              <div className="hidden sm:block" aria-hidden />
              <Label>
                First name
                <Input
                  className="mt-1.5"
                  name="first_name"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="Alex"
                  autoComplete="given-name"
                />
              </Label>
              <Label>
                Last name
                <Input
                  className="mt-1.5"
                  name="last_name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Morgan"
                  autoComplete="family-name"
                />
              </Label>
              <div className="sm:col-span-2">
                <Button type="submit" loading={profilePending} disabled={profilePending}>
                  {profilePending ? "Saving…" : "Save profile"}
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>

        {/* Password */}
        <Card>
          <CardHeader>
            <div>
              <h2 className="text-base font-semibold">Change password</h2>
              <p className="text-sm text-[#65716a]">Minimum 10 characters. You will be asked to log in again.</p>
            </div>
          </CardHeader>
          <CardBody>
            {passwordError && <Alert variant="error" className="mb-4">{passwordError}</Alert>}
            {passwordMessage && <Alert variant="success" className="mb-4">{passwordMessage}</Alert>}
            <form onSubmit={handlePasswordSubmit} className="grid gap-4">
              <Label>
                Current password
                <Input
                  className="mt-1.5"
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  placeholder="Current password"
                />
              </Label>
              <Label>
                New password
                <Input
                  className="mt-1.5"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={10}
                  autoComplete="new-password"
                  placeholder="At least 10 characters"
                />
              </Label>
              <Label>
                Confirm new password
                <Input
                  className="mt-1.5"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={10}
                  autoComplete="new-password"
                  placeholder="Repeat new password"
                />
              </Label>
              <div>
                <Button type="submit" loading={passwordPending} disabled={passwordPending}>
                  {passwordPending ? "Updating…" : "Update password"}
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>

        {/* Company */}
        <Card>
          <CardHeader>
            <div>
              <h2 className="text-base font-semibold">Company settings</h2>
              <p className="text-sm text-[#65716a]">Manage your company identity and operating defaults.</p>
            </div>
          </CardHeader>
          <CardBody>
            {companyError && <Alert variant="error" className="mb-4">{companyError}</Alert>}
            {companyMessage && <Alert variant="success" className="mb-4">{companyMessage}</Alert>}
            {current ? (
              <form onSubmit={handleUpdateCompany} className="grid gap-5 sm:grid-cols-2">
                <Label className="sm:col-span-2">
                  Company name
                  <Input className="mt-1.5" name="name" defaultValue={current.name} required />
                </Label>
                <Label>
                  Accounting currency
                  <select
                    name="currency_code"
                    defaultValue={current.currency_code}
                    className="mt-1.5 w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2.5 text-sm outline-none focus:border-moss focus:ring-2 focus:ring-moss/15"
                  >
                    <option value="UZS">UZS</option>
                    <option value="USD">USD</option>
                  </select>
                </Label>
                <Label>
                  Timezone
                  <Input className="mt-1.5" name="timezone" defaultValue="Asia/Tashkent" required />
                </Label>
                <div className="sm:col-span-2">
                  <Button type="submit" loading={companyPending} disabled={companyPending}>
                    {companyPending ? "Saving…" : "Save settings"}
                  </Button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleCreateCompany} className="grid gap-5 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <h3 className="text-base font-bold">Create your company</h3>
                  <p className="mt-1 text-sm text-[#65716a]">You&apos;ll become the workspace owner.</p>
                </div>
                <Label className="sm:col-span-2">
                  Company name
                  <Input className="mt-1.5" name="name" required placeholder="KRCraft Construction" />
                </Label>
                <Label>
                  Workspace slug <span className="font-normal text-[#849088]">optional</span>
                  <Input className="mt-1.5" name="slug" placeholder="krcraft" />
                </Label>
                <Label>
                  Accounting currency
                  <select
                    name="currency_code"
                    defaultValue="UZS"
                    className="mt-1.5 w-full rounded-lg border border-[#d8ded8] bg-white px-3 py-2.5 text-sm outline-none focus:border-moss focus:ring-2 focus:ring-moss/15"
                  >
                    <option value="UZS">UZS</option>
                    <option value="USD">USD</option>
                  </select>
                </Label>
                <Label className="sm:col-span-2">
                  Timezone
                  <Input className="mt-1.5" name="timezone" defaultValue="Asia/Tashkent" required />
                </Label>
                <div className="sm:col-span-2">
                  <Button type="submit" loading={companyPending} disabled={companyPending}>
                    {companyPending ? "Creating…" : "Create workspace"}
                  </Button>
                </div>
              </form>
            )}
          </CardBody>
        </Card>
      </div>
    </Shell>
  );
}
