/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    basePath: process.env.UI_BASE_PATH || '/chat/ui',
    assetPrefix: process.env.UI_BASE_PATH || '/chat/ui',
};

nextConfig.experimental = {
    missingSuspenseWithCSRBailout: false
}

export default nextConfig;
