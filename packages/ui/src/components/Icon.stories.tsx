import type { Meta, StoryObj } from "@storybook/react-vite";
import { Icon } from "./Icon.js";

// A plus glyph — enough to exercise sizing and the a11y label paths.
const PlusPaths = (
  <>
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </>
);

const meta = {
  title: "Components/Icon",
  component: Icon,
  argTypes: {
    size: { control: "radio", options: [16, 20, 24, 32] },
    label: { control: "text" },
  },
} satisfies Meta<typeof Icon>;
export default meta;

type Story = StoryObj<typeof meta>;

export const Decorative: Story = {
  args: { children: PlusPaths },
};

export const Labeled: Story = {
  args: { label: "Add task", children: PlusPaths },
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      {([16, 20, 24, 32] as const).map((size) => (
        <Icon key={size} size={size} label={`size ${size}`}>
          {PlusPaths}
        </Icon>
      ))}
    </div>
  ),
};
