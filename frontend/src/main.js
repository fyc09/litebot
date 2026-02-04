import { createApp } from 'vue'
import App from './App.vue'
import './style.css'
import TDesign from 'tdesign-vue-next'
import 'tdesign-vue-next/es/style/index.css'
import TdesignChat from '@tdesign-vue-next/chat'

const app = createApp(App)

document.documentElement.setAttribute('theme-mode', 'dark');

app.use(TDesign)
app.use(TdesignChat)

app.mount('#app')
