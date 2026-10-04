import { AuthFormSkeleton } from "@/features/auth/components/auth-form-skeleton";

export default function RegisterLoading() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <AuthFormSkeleton />
    </main>
  );
}
