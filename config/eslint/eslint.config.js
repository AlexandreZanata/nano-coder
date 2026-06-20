export default [
  {
    files: ["**/*.mjs"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
    },
    rules: {
      "no-var": "error",
      "prefer-const": "error",
      "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
      "no-eval": "error",
      "no-implied-eval": "error",
    },
  },
];
