/** @type {import('next').NextConfig} */
const nextConfig = {
	output: "standalone",
	eslint: {
		ignoreDuringBuilds: true,
	},
	images: {
		unoptimized: true,
	},
	typescript: {
		ignoreBuildErrors: true,
	},
};

export default nextConfig;
