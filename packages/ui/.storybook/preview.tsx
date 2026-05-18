import type { Preview } from "@storybook/react-vite";
import "./preview.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: { color: /(background|color)$/i, date: /Date$/i },
    },
    backgrounds: {
      default: "surface",
      values: [
        { name: "surface", value: "oklch(0.99 0 0)" },
        { name: "muted", value: "oklch(0.96 0 0)" },
        { name: "dark", value: "oklch(0.16 0 0)" },
      ],
    },
  },
};

export default preview;
