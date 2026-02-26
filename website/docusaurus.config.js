// @ts-check

const config = {
  title: 'Cifra Docs',
  tagline: 'SEO pipeline для WordPress: фото → контент → CSV → QA',
  favicon: 'img/favicon.svg',

  url: 'https://example.com',
  baseUrl: '/',

  organizationName: 'homgorn',
  projectName: 'cifra',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'ru',
    locales: ['ru'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          routeBasePath: 'docs',
        },
        blog: false,
        pages: true,
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      },
    ],
  ],

  themeConfig: {
    image: 'img/social-card.svg',
    navbar: {
      title: 'Cifra Docs',
      logo: {
        alt: 'Cifra logo',
        src: 'img/logo.svg',
      },
      items: [
        {to: '/docs/intro', label: 'Документация', position: 'left'},
        {to: '/docs/roadmap', label: 'Roadmap', position: 'left'},
        {href: 'https://github.com/homgorn/cifra', label: 'GitHub', position: 'right'},
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {label: 'Быстрый старт', to: '/docs/intro'},
            {label: 'CSV схема', to: '/docs/wp-all-import-schema'},
          ],
        },
        {
          title: 'Project',
          items: [{label: 'Roadmap', to: '/docs/roadmap'}],
        },
      ],
      copyright: `© ${new Date().getFullYear()} Cifra. SEO-first docs on Docusaurus.`,
    },
    metadata: [
      {
        name: 'description',
        content:
          'Полная документация Cifra на Docusaurus: SEO-подготовка медиа, WP All Import CSV, валидатор и QA.',
      },
      {name: 'keywords', content: 'Docusaurus, SEO, WordPress, WP All Import, CSV, pipeline'},
      {name: 'robots', content: 'index,follow,max-image-preview:large'},
      {property: 'og:type', content: 'website'},
      {property: 'og:locale', content: 'ru_RU'},
    ],
  },
};

module.exports = config;
