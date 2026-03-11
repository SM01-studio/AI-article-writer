/**
 * AI Article Writer - 前端配置
 *
 * 在生产环境中，修改此文件中的 API_BASE_URL 为后端服务器地址
 */

(function() {
    'use strict';

    // API 基础地址配置
    // 开发环境: 使用本地后端
    // 生产环境: 修改为你的后端服务器地址

    // ⬇️ 生产环境部署时，修改下面的地址 ⬇️
    window.API_BASE_URL = window.API_BASE_URL || 'http://localhost:5000/api';

    // 示例：生产环境配置
    // window.API_BASE_URL = 'https://api.your-domain.com/api';

    console.log('🔗 API Base URL:', window.API_BASE_URL);

})();
