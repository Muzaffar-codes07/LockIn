import type { Meta, StoryObj } from "@storybook/react-vite";
import { Input } from "./Input.js";

const meta = {
  title: "Components/Input",
  component: Input,
  args: { placeholder: "Type a task title…" },
  argTypes: {
    invalid: { control: "boolean" },
    disabled: { control: "boolean" },
  },
} satisfies Meta<typeof Input>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
export const Invalid: Story = { args: { invalid: true, defaultValue: "bad value" } };
export const Disabled: Story = { args: { disabled: true, defaultValue: "locked" } };
