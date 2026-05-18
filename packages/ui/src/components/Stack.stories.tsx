import type { Meta, StoryObj } from "@storybook/react-vite";
import { Stack } from "./Stack.js";

const swatch = (label: string) => (
  <div key={label} className="rounded-md bg-brand-500 px-4 py-2 text-white">
    {label}
  </div>
);

const meta = {
  title: "Components/Stack",
  component: Stack,
  argTypes: {
    direction: { control: "radio", options: ["row", "col"] },
    gap: { control: "select", options: [1, 2, 3, 4, 6, 8, 12] },
    align: { control: "radio", options: ["start", "center", "end", "stretch"] },
    justify: { control: "radio", options: ["start", "center", "end", "between"] },
  },
} satisfies Meta<typeof Stack>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Column: Story = {
  args: { direction: "col", gap: 4 },
  render: (args) => <Stack {...args}>{["One", "Two", "Three"].map(swatch)}</Stack>,
};

export const Row: Story = {
  args: { direction: "row", gap: 3 },
  render: (args) => <Stack {...args}>{["One", "Two", "Three"].map(swatch)}</Stack>,
};
