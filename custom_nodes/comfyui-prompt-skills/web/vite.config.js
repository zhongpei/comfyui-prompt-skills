import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
    plugins: [vue()],
    build: {
        outDir: '../js',
        emptyOutDir: false,
        lib: {
            entry: path.resolve(__dirname, 'src/main.js'),
            name: 'PromptSkillsVue',
            fileName: (format) => `prompt-skills.${format}.js`,
            formats: ['es']
        },
        rollupOptions: {
            external: ['/scripts/app.js', '/scripts/api.js'],
            output: {
                globals: {
                    '/scripts/app.js': 'app'
                }
            }
        }
    },
    define: {
        'process.env': {}
    }
})
