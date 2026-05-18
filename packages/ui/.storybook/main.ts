import type { StorybookConfig } from "@storybook/react-vite";

const config: StorybookConfig = {
  // Storybook 9+ folds the former addon-essentials (controls, actions,
  // viewport, backgrounds, docs) into core — no separate addon install.
  stories: ["../src/**/*.stories.@(ts|tsx)"],
  framework: { name: "@storybook/react-vite", options: {} },
  typescript: { reactDocgen: "react-docgen-typescript" },
  async viteFinal(viteConfig) {
    // Tailwind v4 is a Vite plugin — Storybook doesn't pick it up from
    // postcss.config like the Next app does, so we register it here.
    const { default: tailwindcss } = await import("@tailwindcss/vite");
    viteConfig.plugins = viteConfig.plugins ?? [];
    viteConfig.plugins.push(tailwindcss());
    return viteConfig;
  },
};

export default config;
