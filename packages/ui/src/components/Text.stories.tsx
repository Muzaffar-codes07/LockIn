import type { Meta, StoryObj } from "@storybook/react-vite";
import { Text } from "./Text.js";

const meta = {
  title: "Components/Text",
  component: Text,
  args: { children: "The quick brown fox" },
  argTypes: {
    size: { control: "select", options: ["xs", "sm", "base", "lg", "xl", "2xl", "3xl"] },
    tone: { control: "radio", options: ["default", "muted", "danger", "success"] },
    weight: { control: "radio", options: ["normal", "medium", "semibold", "bold"] },
  },
} satisfies Meta<typeof Text>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Muted: Story = { args: { tone: "muted" } };

export const Scale: Story = {
  render: () => (
    <div className="flex flex-col gap-1">
      {(["xs", "sm", "base", "lg", "xl", "2xl", "3xl"] as const).map((size) => (
        <Text key={size} size={size}>
          {size} — The quick brown fox
        </Text>
      ))}
    </div>
  ),
};
