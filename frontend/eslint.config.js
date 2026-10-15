import prettier from 'eslint-config-prettier';
import js from '@eslint/js';
import { includeIgnoreFile } from '@eslint/compat';
import svelte from 'eslint-plugin-svelte';
import globals from 'globals';
import { fileURLToPath } from 'node:url';

const gitignorePath = fileURLToPath(new URL('./.gitignore', import.meta.url));

export default [
  includeIgnoreFile(gitignorePath),
  js.configs.recommended,
  ...svelte.configs.recommended,
  prettier,
  ...svelte.configs.prettier,
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node }
    }
  },
  {
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
      'no-useless-assignment': 'warn',
      'svelte/require-each-key': 'warn',
      'svelte/no-navigation-without-resolve': 'warn',
      'svelte/prefer-svelte-reactivity': 'warn',
      'svelte/prefer-writable-derived': 'warn'
    }
  }
];
