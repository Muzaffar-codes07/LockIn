import { redirect } from "next/navigation";
import { auth, signIn } from "@/auth";
import { Button, Stack, Text } from "@lockin/ui";

export default async function Home() {
  const session = await auth();
  if (session) {
    redirect("/dashboard");
  }

  return (
    <main className="min-h-dvh grid place-items-center">
      <Stack gap={4} align="center">
        <Text as="h1" size="3xl" weight="bold">
          LockIn
        </Text>
        <Text tone="muted">Mood-aware productivity. Sign in to start.</Text>
        <form
          action={async () => {
            "use server";
            await signIn("google", { redirectTo: "/dashboard" });
          }}
        >
          <Button type="submit" variant="primary">
            Sign in with Google
          </Button>
        </form>
      </Stack>
    </main>
  );
}
