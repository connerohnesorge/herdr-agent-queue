// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
	site: 'https://connerohnesorge.github.io',
	base: '/herdr-agent-queue',
	integrations: [
		starlight({
			title: 'herdr-agent-queue',
			description: 'Queue prompts for coding agents in herdr and submit each one when the current turn ends.',
			social: [{ icon: 'github', label: 'GitHub', href: 'https://github.com/connerohnesorge/herdr-agent-queue' }],
			editLink: { baseUrl: 'https://github.com/connerohnesorge/herdr-agent-queue/edit/main/docs/' },
			sidebar: [
				{
					label: 'Guides',
					items: [
						{ label: 'Install', slug: 'guides/install' },
						{ label: 'Usage', slug: 'guides/usage' },
						{ label: 'Skill completion', slug: 'guides/skill-completion' },
					],
				},
				{
					label: 'Reference',
					items: [
						{ label: 'How it works', slug: 'reference/how-it-works' },
						{ label: 'Troubleshooting', slug: 'reference/troubleshooting' },
						{ label: 'Development', slug: 'reference/development' },
					],
				},
			],
		}),
	],
});
