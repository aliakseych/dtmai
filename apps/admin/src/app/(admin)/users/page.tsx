"use client";
import { useState } from "react";
import { PageHeader } from "@/components/ui/controls";
import { UserDrawer } from "@/components/users/UserDrawer";
import { UsersTable } from "@/components/users/UsersTable";
import { useAuth } from "@/lib/auth";
import { ALL_ROLES, type AdminUser } from "@/lib/users";

export default function UsersPage() {
  const { isAdmin } = useAuth();
  const [sel, setSel] = useState<AdminUser | null>(null);
  return (
    <>
      <PageHeader title="Users" sub="Search, filter and manage learners and staff; open a row for roles, status and statistics." />
      <UsersTable queryKey="users" roles={ALL_ROLES} role="" allowAnyRole onOpen={setSel} selected={sel?.id} />
      <UserDrawer user={sel} onClose={() => setSel(null)} canEdit={isAdmin} />
    </>
  );
}
