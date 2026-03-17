/**
 * AI Article Writer - 前端配置
 *
 * 在生产环境中，修改此文件中的 API_BASE_URL 为后端服务器地址
 */

(function() {
    'use strict';

    // API 基础地址配置
    // 生产环境: 使用云服务器后端
    // 开发环境: 使用本地后端

    // 检测是否在 Vercel 生产环境
    const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

    // 生产环境配置 - 指向云服务器 API (HTTPS)
    if (isProduction) {
        window.API_BASE_URL = 'https://api.siliang.cfd/api/writer';
        // 主门户 API（用于登录验证）
        window.AUTH_API_URL = 'https://api.siliang.cfd/api/auth';
        // 主门户登录页
        window.LOGIN_URL = 'https://siliang.cfd/index.html';
    } else {
        // 开发环境配置 - 使用本地 API
        window.API_BASE_URL = 'http://localhost:5000/api';
        // 本地开发跳过登录验证
        window.AUTH_API_URL = null;
        window.LOGIN_URL = null;
    }

    console.log('🔗 API Base URL:', window.API_BASE_URL);
    console.log('🔐 Auth API URL:', window.AUTH_API_URL);
    console.log('🌍 Environment:', isProduction ? 'Production' : 'Development');

})();
