module.exports = {
  extends: [
    'react-app',
    'react-app/jest'
  ],
  rules: {
    // 禁用一些严格的规则以便快速开发
    'react/jsx-no-undef': 'off',
    '@typescript-eslint/no-unused-vars': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/ban-ts-comment': 'off',
    'no-unused-vars': 'off',
    'prefer-const': 'off',
    'no-console': 'off',
    'react-hooks/exhaustive-deps': 'warn',
    // 允许any类型
    '@typescript-eslint/no-unsafe-assignment': 'off',
    '@typescript-eslint/no-unsafe-member-access': 'off',
    '@typescript-eslint/no-unsafe-call': 'off',
    '@typescript-eslint/no-unsafe-return': 'off',
    // 允许空函数
    '@typescript-eslint/no-empty-function': 'off',
    // 允许require
    '@typescript-eslint/no-var-requires': 'off'
  }
};
