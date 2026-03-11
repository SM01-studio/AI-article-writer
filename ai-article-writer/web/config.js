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

    // 生产环境配置 - 指向云服务器 API
    if (isProduction) {
        window.API_BASE_URL = 'http://47.79.0.228/api';
    } else {
        // 开发环境配置 - 使用本地 API
        window.API_BASE_URL = 'http://localhost:5000/api';
    }

    console.log('🔗 API Base URL:', window.API_BASE_URL);
    console.log('🌍 Environment:', isProduction ? 'Production' : 'Development');

})();
