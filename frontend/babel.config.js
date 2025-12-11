export default {
  presets: [
    ["@babel/preset-env", { targets: { node: "current" } }],
    ["@babel/preset-react", { runtime: "automatic" }],
    "@babel/preset-typescript",
  ],
  plugins: [
    "@babel/plugin-syntax-import-meta",
    [
      "babel-plugin-transform-vite-meta-env",
      {
        env: {
          VITE_API_URL: "http://localhost:8000",
        },
      },
    ],
  ],
};
