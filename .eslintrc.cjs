module.exports = {
  // Specifies the ESLint parser
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020, // Allows for the parsing of modern ECMAScript features
    sourceType: 'module', // Allows for the use of imports
    ecmaFeatures: {
      jsx: false, // Disables JSX since it's not used in Node.js
    },
  },
  settings: {
    react: {
      version: 'detect', // React version. "detect" automatically picks the version you have installed.
    },
  },
  env: {
    browser: false, // Node.js project not for browser
    es2021: true,
    node: true, // Enables Node.js global variables
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended', // Uses the recommended rules from the @typescript-eslint/eslint-plugin
  ],
  rules: {
    // Place to specify ESLint rules. Can be used to overwrite rules specified from the extended configs
    // e.g., "@typescript-eslint/explicit-function-return-type": "off",
  },
  overrides: [
    {
      files: ['*.js'], // Override settings for JavaScript files
      rules: {
        '@typescript-eslint/no-var-requires': 'off', // Allow require() in JavaScript files
      },
    },
  ],
};
