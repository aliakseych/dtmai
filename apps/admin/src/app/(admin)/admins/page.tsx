"use client";
import { useState } from "react";
import { Btn, PageHeader } from "@/components/ui/controls";
import { CreateStaffDialog } from "@/components/users/CreateStaffDialog";
import { UserDrawer } from "@/components/users/UserDrawer";
import { UsersTable } from "@/components/users/UsersTable";
import { useAuth } from "@/lib/auth";
import { STAFF_ROLES, type AdminUser } from "@/lib/users";

export default function AdminsPage() {
  const { isAdmin } = useAuth();
  const [sel, setSel] = useState<AdminUser | null>(null);
  const [creating, setCreating] = useState(false);
  return (
    <>
      <PageHeader title="Admins & staff" sub="Accounts with staff roles. Admins can create accounts and change roles." />
      <UsersTable queryKey="staff" roles={STAFF_ROLES} role="admin" allowAnyRole={false} onOpen={setSel} selected={sel?.id}
        toolbarExtra={isAdmin && <Btn variant="primary" onClick={() => setCreating(true)}>Create staff account</Btn>} />
      <CreateStaffDialog open={creating} onClose={() => setCreating(false)} />
      <UserDrawer user={sel} onClose={() => setSel(null)} canEdit={isAdmin} />
    </>
  );
}
