import type { Meta, StoryObj } from "@storybook/react-vite";
import { Card } from "./Card.js";

const meta = {
  title: "Components/Card",
  component: Card,
} satisfies Meta<typeof Card>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="max-w-sm">
      <h3 className="text-lg font-semibold text-text">Card title</h3>
      <p className="text-text-muted">
        Cards group related content with a border, padding, and a subtle shadow.
      </p>
    </Card>
  ),
};
