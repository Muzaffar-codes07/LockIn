import { Button, Stack, Text } from "@lockin/ui";

export default function Home() {
  return (
    <main className="min-h-dvh grid place-items-center">
      <Stack gap={4} align="center">
        <Text as="h1" size="3xl" weight="bold">
          LockIn
        </Text>
        <Text tone="muted">Foundation slice — design system smoke test.</Text>
        <Button variant="primary">Press Cmd+K (Week 3)</Button>
      </Stack>
    </main>
  );
}
