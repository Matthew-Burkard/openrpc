const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Python OpenRPC',
  tagline: 'Develop quick and easy OpenRPC API in Python.',
  favicon: 'img/logo.svg',

  url: 'https://python-openrpc.burkard.cloud',
  baseUrl: '/',

  projectName: 'python-openrpc',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
        '@docusaurus/preset-classic',
        {
            docs: {
                routeBasePath: '/',
            },
        },
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'Python OpenRPC',
        logo: {
          alt: 'Python OpenRPC Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            href: 'https://gitlab.com/mburkard/openrpc',
            label: 'GitLab',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Intro',
                to: '/',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitLab',
                href: 'https://gitlab.com/mburkard/openrpc',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Matthew Burkard. Built with Docusaurus.`,
      },
      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
      },
    }),
};

module.exports = config;
