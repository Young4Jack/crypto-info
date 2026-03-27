import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/Login.vue')
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/alerts',
      name: 'Alerts',
      component: () => import('../views/Alerts.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/assets',
      name: 'Assets',
      component: () => import('../views/Assets.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/watchlist',
      name: 'Watchlist',
      component: () => import('../views/Watchlist.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/Settings.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/public',
      name: 'PublicWatchlist',
      component: () => import('../views/PublicWatchlist.vue')
    },
    {
      path: '/',
      redirect: '/public'
    }
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router